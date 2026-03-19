# Universal Commerce Protocol (UCP) Connector

The gateway between Odoo and the Global AI Commerce Mesh.

## 🚀 Overview
This module implements the **Universal Commerce Protocol (UCP)** standard. It allows your Odoo store to be "discovered" and "navigated" by Generative AI agents (like Google Gemini and others) looking to fulfill orders for users.

## ✨ Key Features
- **Headless Checkout API**: Exposes `/ucp/v1/checkout-sessions` following the standard specification.
- **Native Data Mapping**: Translates UCP schemas (Cart, Shipping, Billing) directly into Odoo Sales Orders.
- **Inventory Visibility**: Provides real-time stock and pricing feedback to external agents.
- **Security**: Controlled access via Bearer Tokens and secure session tokens.

## 📦 Installation
1. Install the module via Odoo Apps.
2. In **Settings > General Settings**, locate the UCP section.
3. Generate or configure your Bearer Tokens for authorized agents.

## 👨‍💻 Author
**TMFCoders SL**  
[tmfcoders.com](https://tmfcoders.com)  

## 📄 License
Licensed under **OPL-1**.
