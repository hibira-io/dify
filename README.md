# Hibira for Dify

**Author:** hibira
**Version:** 0.1.0
**Type:** tool
**Source:** https://github.com/hibira-io/dify

Give your Dify workflows, chatflows and agents a realtime channel to your users and a human in the loop:

- **Publish Event** sends a realtime event to every browser or app subscribed to one or more channels (live dashboards, progress updates, notifications in an open page).
- **Send Push Notification** reaches iOS, Android and web devices by interest or by user ID.
- **Request Approval** asks a person to approve or reject a step through a Hibira-hosted answer page, and can wait up to 9 minutes for the decision.
- **Get Approval** reads the answer later, or waits for it.

[Hibira](https://hibira.io) is a hosted realtime service with a Pusher-compatible API.

## Setup

1. Sign in at [hibira.io](https://hibira.io/portal/) (the Free plan is enough to try it) and create an app.
2. On the app page, copy the **App ID**, **Key** and **Secret**.
3. To send push notifications, enable Push on the app and copy the **Push Instance ID** and **Push Secret Key** from its Push section. Skip this if you only need events and approvals.
4. In Dify, install the plugin, open **Tools → Hibira → Authorize** and paste the values. Saving checks them against the Hibira API.

Requests go to `https://ws.hibira.io` over HTTPS. Approvals need an app in a Hibira account (not a self-hosted server).

## Tools

### Publish Event

| Parameter | Description |
| --- | --- |
| Channels | Comma-separated channel names, at most 100 |
| Event Name | The event your clients listen for, such as `order-updated` |
| Data | Event payload, usually JSON text, at most 10 KB |
| Exclude Socket ID | Optional connection that should not receive it |

Clients receive it with any Pusher-compatible client library, for example:

```js
const hibira = new Pusher('YOUR_KEY', {
  cluster: 'hkg',
  wsHost: 'ws.hibira.io',
  wsPort: 443,
  wssPort: 443,
  forceTLS: true,
  enabledTransports: ['ws', 'wss'],
});
hibira.subscribe('orders').bind('order-updated', (data) => console.log(data));
```

### Send Push Notification

Choose **Interests** (topics devices subscribed to) or **User IDs**, then set a title, text, an optional https link for web notifications and optional custom JSON data. One notification goes to iOS (APNs), Android (FCM) and web at once.

### Request Approval

Creates an approval request and returns `approval_id`, the answer `url` and `status`. Share the link, or let Hibira deliver it with **Push to Interests** / **Push to User IDs**, or to your own approvals inbox with **Inbox Channel**. Anyone with the link can answer, and the first answer counts.

- **Options**: 2 to 4 choices, default `Approve, Reject`. The first one approves.
- **Wait for Answer**: 0 to 9 minutes (default 5). When the time runs out the status is still `pending`; use Get Approval later.
- **Link Expires In**: 1 minute to 7 days (default 60 minutes).

`status` is `approved` (first option chosen), `rejected` (another option), `pending` or `expired`. Answered requests include `choice`, `answered_at` and any `comment`.

A typical workflow: Request Approval → IF/ELSE on `status == approved` → do the risky step.

### Get Approval

Pass the `approval_id` from Request Approval. Optionally wait 0 to 9 minutes while it is pending.

## Limits

Plan limits on messages, connections and push apply as on the [pricing page](https://hibira.io/pricing). New approval requests are limited to 1 per second (burst 20) per account.

## Privacy

See [PRIVACY.md](PRIVACY.md). The plugin stores nothing and only talks to `ws.hibira.io`.

## Support

- Issues: https://github.com/hibira-io/dify/issues
- Email: dev@hibira.io
- Chinese summary: https://github.com/hibira-io/dify/blob/main/docs/README.zh-TW.md
