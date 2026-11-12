# Hibira for Dify（中文摘要）

Dify 工具外掛，讓工作流、Chatflow 和 Agent 可以：

- **發布事件（Publish Event）**：即時推送事件給訂閱頻道的瀏覽器或 App。
- **發送推播（Send Push Notification）**：依 interests 或使用者 ID 推播到 iOS、Android、網頁。
- **發起審批（Request Approval）**：透過 Hibira 託管的回覆頁請人批准或拒絕，最多可等待 9 分鐘。
- **查詢審批（Get Approval）**：之後再讀取或等待回覆。

設定：在 [hibira.io](https://hibira.io/portal/) 建立 app，把 App ID、Key、Secret（推播另需 Push Instance ID 和 Push Secret Key）填進 Dify 的 Hibira 授權。只會連線到 `https://ws.hibira.io`。

打包：`scripts/package.sh` 產生 `dist/hibira-<版本>.difypkg`；推送 `v<版本>` 標籤時 CI 會把它附到 GitHub Release。完整說明見 [README.md](../README.md)。
