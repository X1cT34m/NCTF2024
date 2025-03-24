use std::{net::SocketAddr, sync::Arc};

use anyhow::anyhow;
use axum::{
    Form, Json,
    extract::{ConnectInfo, Query, State},
    response::Html,
};
use serde_json::{Value, json};
use tokio::task;

use crate::{
    bot,
    db::{self, DbPool},
    error::AppError,
    model::{Report, Search},
};

pub async fn index() -> Html<String> {
    let content = include_str!("../public/index.html");
    Html(content.to_string())
}

pub async fn report(Form(report): Form<Report>) -> Json<Value> {
    task::spawn(async move { bot::visit_url(report.url).await.unwrap() });

    Json(json!({
        "message": "bot will visit the url soon"
    }))
}

pub async fn public_search(
    Query(search): Query<Search>,
    State(pool): State<Arc<DbPool>>,
) -> Result<Json<Vec<String>>, AppError> {
    let pool = pool.clone();
    let conn = pool.get()?;
    let comments = db::search(conn, search.s, false)?;

    if comments.len() > 0 {
        Ok(Json(comments))
    } else {
        Err(anyhow!("No comments found").into())
    }
}

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
