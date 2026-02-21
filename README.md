# Universal Commerce Protocol (UCP) Connector for Odoo

This module transforms any Odoo 18 eCommerce instance into an AI-ready transaction endpoint by implementing the **Google Universal Commerce Protocol (UCP)**.

**Created by**: TMFCoders SL

## Features
- Full compliance with UCP capabilities mapping.
- Native conversion of UCP JSON to Odoo `sale.order`.
- Complete Webhooks implementation mapping.
- Secure, tokenized payment handling compatible with Odoo 18 payment flows.

## Usage
Simply install the module. It exposes `/ucp/v1/checkout-sessions` secured by Odoo's native API Keys authentication. AI Agents connecting to this endpoint will be able to complete checkouts natively.
