---
title: "Domain URL and Hosting"
category: "Web Development"
level: "Beginner"
type: "Knowledge"
status: "Complete"
---

# Domain, URL, and Hosting

## Definition
A **domain** is a human-readable name (e.g. `example.com`) mapped to a server's IP address via [[DNS]]. A **URL** is the full address of a specific resource, including protocol, domain, path, and optional query string. **Hosting** is the infrastructure that serves your site or application to the internet.

## Core Concepts
- **URL structure**: `scheme://host:port/path?query#fragment`
- **Domain vs subdomain**: `example.com` vs `api.example.com`
- **Hosting types**: static hosting, shared hosting, VPS, cloud hosting, [[Serverless]]

## How It Works
A browser resolves the domain in a URL to an IP address via DNS, opens a TCP/TLS connection to that IP on the given port, and sends an HTTP request for the given path. The hosting provider's server (or CDN edge node) returns the response.

## Mermaid Diagram
```mermaid
flowchart LR
    URL["https://example.com/products?id=1"] --> Scheme[https]
    URL --> Host[example.com]
    URL --> Path[/products]
    URL --> Query["id=1"]
    Host --> DNS[DNS Lookup] --> IP[Server IP] --> Hosting[Hosting Provider]
```

## Example
`https://shop.example.com:443/cart?item=42#summary`
- scheme: `https`
- subdomain: `shop`
- domain: `example.com`
- port: `443` (implicit for HTTPS)
- path: `/cart`
- query: `item=42`
- fragment: `#summary`

## Real-World Usage
Static sites are often hosted on CDNs (Netlify, Vercel, Cloudflare Pages); dynamic backends on cloud VMs, containers, or serverless platforms; databases on managed services.

## Best Practices
- Always serve production traffic over HTTPS ([[SSL]]/[[HTTPS]]).
- Keep DNS TTLs reasonable to allow timely failover.

## Related Topics
- [[HTTP]]
- [[DNS]]
- [[SSL]]
- [[CDN]]
- [[Deployment]]

## Prerequisites
- [[World Wide Web]]

## Quick Revision
Domain = human-readable name; URL = full resource address; hosting = the infrastructure serving it, resolved via DNS.

## Interview Questions
- Break down the parts of a URL and what each one means.
- What is the difference between a domain and a subdomain?
