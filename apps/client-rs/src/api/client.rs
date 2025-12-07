pub struct MyClient {
    pub client: reqwest::Client,
}

impl MyClient {
    pub async fn healthcheck(&self) -> String {
        let response = self
            .client
            .get("http://localhost:8000/api/v1/health")
            .send()
            .await;

        let text = response.unwrap().text().await.unwrap();

        text
    }
}
