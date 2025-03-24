use std::{fs, path::Path};

use r2d2::{Pool, PooledConnection};
use r2d2_sqlite::SqliteConnectionManager;
use rusqlite::params;

pub type DbPool = Pool<SqliteConnectionManager>;
pub type DbConn = PooledConnection<SqliteConnectionManager>;

pub fn init(db_name: String, json_name: String, flag: String) -> anyhow::Result<DbPool> {
    if Path::new(&db_name).exists() {
        fs::remove_file(&db_name)?;
    }

    let manager = SqliteConnectionManager::file(db_name);
    let pool = Pool::new(manager)?;

    let content = fs::read_to_string(json_name)?;
    let comments: Vec<String> = serde_json::from_str(&content)?;

    let conn = pool.get()?;
    conn.execute(
        "CREATE TABLE comments(content TEXT, hidden BOOLEAN)",
        params![],
    )?;

    for comment in comments {
        conn.execute(
            "INSERT INTO comments(content, hidden) VALUES(?, ?)",
            params![comment, false],
        )?;
    }

    conn.execute(
        "INSERT INTO comments(content, hidden) VALUES(?, ?)",
        params![flag, true],
    )?;

    Ok(pool)
}

pub fn search(conn: DbConn, query: String, hidden: bool) -> anyhow::Result<Vec<String>> {
    let mut stmt =
        conn.prepare("SELECT content FROM comments WHERE content LIKE ? AND hidden = ?")?;
    let comments = stmt
        .query_map(params![format!("%{}%", query), hidden], |row| {
            Ok(row.get(0)?)
        })?
        .collect::<rusqlite::Result<Vec<String>>>()?;

    Ok(comments)
}
