# Universal Commerce Protocol (UCP) Connector for Odoo

This module transforms any Odoo 18 eCommerce instance into an AI-ready transaction endpoint by implementing the **Google Universal Commerce Protocol (UCP)**.

**Created by**: TMFCoders SL

## Features
- Full compliance with UCP capabilities mapping.
- Native conversion of UCP JSON to Odoo `sale.order`.
- Complete Webhooks implementation mapping.
- Secure, tokenized payment handling compatible with Odoo 18 payment flows.

## Usage
Simply install the module. It exposes `/ucp/v1/checkout-sessions` secured by OAuth 2.0 Bearer Identity Linking. AI Agents connecting to this endpoint will be able to complete checkouts natively and link their actions to an Odoo User.

## ToDo / Roadmap (UCP Advanced Extensions)
While the core "Native Checkout REST", Identity Linking, and Discovery profiles are supported, the following capabilities are planned for future releases to achieve full UCP spec compliance:
- **`dev.ucp.shopping.fulfillment`**: Expose shipping methods, pickup locations, delivery estimates, and option groups.
- **`dev.ucp.shopping.discounts`**: Support for injecting and reconciling coupon codes and gift cards.
- **`dev.ucp.shopping.ap2_mandate`**: Cryptographic non-repudiation via JWS signatures for Merchant Authorization.
- **`dev.ucp.shopping.order` (Webhooks)**: Push full order lifecycle events (shipped, delivered, canceled) to the platform's webhook endpoint properly encoded and signed.
