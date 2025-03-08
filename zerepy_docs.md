### ZerePy Server Setup

AuditOne has set up the **ZerePy Server** with **market stats** and **security stats** features integrated into the **Sonic connection**.

ZerePy is a modular framework for agents on-chain that is configured with various services to run agents and for the Sonic's Risk Watch, the following actions are registered 

- **Market Stats**: Gathered from **Dex Screener API**.
- **Security Stats**: Fetched from **AuditOne API**.

These data points are processed through the **Sonic connection**, enabling real-time analytics for risk assessment.

The diagram below outlines the **ZerePy Server setup**:
<center>
<img src="static/img/zerepy_server.png" alt="ZerePy Server Diagram" width="600">
</center>


##### **Data Sources**
- **AuditOne API**: Collects security insights, audit data, and vulnerability reports.
- **Dex Screener API**: Fetches token performance, trading volume, and liquidity metrics.
- **Contest Platforms**: Sources audit data from **Cantina, Sherlock, Code4rena** and etc...
- **Hack Data Providers**: Uses past exploit records from **Rekt** and **SlowMist**.

##### **Data Flow**
1. **Market & Security Data Collection**  
   - AuditOne API and Dex Screener API push data into the **Sonic connection**.

2. **Processing via ZerePy Framework**  
   - ZerePy aggregates, analyzes, and standardizes risk metrics.

3. **Deployment Using Docker & Render**  
   - The ZerePy Server is containerized with **Docker** and deployed on **Render** for scalability.

4. **APIs Hosted on Heroku**  
   - The **AuditOne API** is hosted on **Heroku** to provide a gateway for security and audit reports.

---

##### **Deployment Stack**
- **Docker**: Containers for ZerePy Framework.
- **Render**: Cloud hosting for the ZerePy Server.
- **Heroku**: API hosting for AuditOne security data.

##### **Useful Links**
- **AuditOne API Docs**: [https://api.auditone.io/](https://api.auditone.io/)
- **ZerePy Server Docs**: [https://zerepy.auditone.io/docs](https://zerepy.auditone.io/docs)

---

##### **Next Steps**
AuditOne wants to actively contribute to the **ZerePy Server** by:

- Adding **more analytics models** for risk classification
- Expanding **data sources** for deeper security insights.
- Enhancing **real-time monitoring** of token vulnerabilities.

If you are interested in **additional features**, submit your request here: <a href="https://forms.gle/6XTshhzjfZ8hyqQh8" target="_blank" rel="noopener noreferrer"><b>Feature Request Form</b></a>