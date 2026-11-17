import "./Footer.css";

function Footer() {
  return (
    <footer className="app-footer">

      <div className="footer-left">

        <div className="footer-brand">
          <span className="footer-brand-mark">
            AI
          </span>

          <span>
            Enterprise AI Workspace
          </span>
        </div>

        <span className="footer-separator">
          •
        </span>

        <span className="footer-description">
          RAG • MCP • Multi-Agent AI
        </span>

      </div>


      <div className="footer-right">

        <span className="footer-status">
          <span className="footer-status-dot" />
          System Ready
        </span>

        <span className="footer-version">
          Prototype v1.0
        </span>

      </div>

    </footer>
  );
}


export default Footer;