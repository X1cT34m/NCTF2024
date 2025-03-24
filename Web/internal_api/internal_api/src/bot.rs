use std::time::Duration;

use fantoccini::ClientBuilder;
use tokio::time;

pub async fn visit_url(url: String) -> Result<(), Box<dyn std::error::Error>> {
    let mut caps = serde_json::map::Map::new();
    let opts = serde_json::json!({
        "args": [
            "--headless",
            "--no-sandbox",
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--remote-debugging-port=9222"
        ],
    });
    caps.insert("goog:chromeOptions".to_string(), opts);

    let c = ClientBuilder::native()
        .capabilities(caps)
        .connect("http://bot:4444")
        .await?;

    println!("visiting {}", url);
    c.goto(&url).await?;

    println!("bot will sleep for 30s");
    time::sleep(Duration::from_secs(30)).await;

    println!("visited {} success", url);
    c.close().await?;

    Ok(())
}
