use std::{env, net::SocketAddr, sync::Arc};

use axum::{
    Router,
    routing::{get, post},
};
use internal_api::{db, route};
use tokio::net::TcpListener;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let db_name = env::var("DB_NAME")?;
    let json_name = env::var("JSON_NAME")?;
    let flag = env::var("FLAG")?;

    let pool = db::init(db_name, json_name, flag)?;
    let app = Router::new()
        .route("/", get(route::index))
        .route("/report", post(route::report))
        .route("/search", get(route::public_search))
        .route("/internal/search", get(route::private_search))
        .with_state(Arc::new(pool));

    let addr = format!("{}:{}", env::var("HOST")?, env::var("PORT")?);
    let listener = TcpListener::bind(addr).await?;
    axum::serve(
        listener,
        app.into_make_service_with_connect_info::<SocketAddr>(),
    )
    .await?;

    Ok(())
}
