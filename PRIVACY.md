# Privacy Policy

The Hibira plugin for Dify sends requests only to the Hibira API at `https://ws.hibira.io`, and only when one of its tools runs.

## What the plugin sends

- **Credentials.** Your app ID and key, and a signature made with your app secret, are sent with each request so Hibira can authenticate it. The Push secret key is sent as a Bearer token for push requests. The secret itself is never sent.
- **Tool input.** The content you or your agent put into a tool: channel names, event names and event data (Publish Event); interests or user IDs, notification title, text, link and custom data (Send Push Notification); the question, details, options and delivery settings of an approval (Request Approval); an approval ID (Get Approval).

## What the plugin stores

Nothing. The plugin has no storage of its own and does not log tool input or credentials. Dify stores your credentials in your Dify workspace as it does for every plugin.

## What Hibira does with the data

Hibira processes events and notifications to deliver them, and keeps approval requests until a day after they expire so their answer can be read. Usage metadata is kept for billing and abuse prevention. See the Hibira privacy policy at https://hibira.io/legal/privacy and the terms at https://hibira.io/legal/terms.

## Third parties

Push notifications are delivered through Apple Push Notification service, Firebase Cloud Messaging or the browser's Web Push service, depending on the device. No other third party receives data from this plugin.

## Contact

dev@hibira.io
