import "./Header.css";

function Header({
  activePage,
  setSidebarOpen,
  onNavigate,
}) {
  const navItems = [
    "Workspace",
    "Documents",
    "Knowledge",
    "Agents",
    "Tasks",
  ];

  return (
    <header className="header">

      {/* =================================================
          MOBILE MENU
      ================================================= */}

      <button
        type="button"
        className="menu-button"
        onClick={() => setSidebarOpen(true)}
        aria-label="Open menu"
      >
        ☰
      </button>


      {/* =================================================
          PRIMARY NAVIGATION
      ================================================= */}

      <nav className="header-navigation">

        {navItems.map((item) => (

          <button
            key={item}
            type="button"
            className={`header-nav-item ${
              activePage === item
                ? "active"
                : ""
            }`}
            onClick={() => {
              if (onNavigate) {
                onNavigate(item);
              }
            }}
          >
            {item}
          </button>

        ))}

      </nav>

    </header>
  );
}

export default Header;