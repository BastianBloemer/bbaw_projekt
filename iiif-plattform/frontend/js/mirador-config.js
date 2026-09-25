export function createConfig({
  manifestId,
  canvasId = null,
}) {

  const windowConfig = {
    manifestId: manifestId,
    thumbnailNavigationPosition: "far-right",
    view: "single",
  };

  if (canvasId) {
    windowConfig.canvasId = canvasId;
  }

  return {
    id: "my-mirador",
    language: "de",
    windows: [windowConfig],
    window: {
      allowClose: false,
      allowFullscreen: true,
      allowMaximize: false,
      allowTopMenuButton: false,
      allowWindowSideBar: true,
      sideBarPanel: 'canvas',
      defaultSidebarPanelWidth: 300,
      hideWindowTitle: true,
      sideBarOpen: false,
      showLocalePicker: true,
      panels: {
        info: false,
        attribution: false,
        canvas: true,
        annotations: false,
        search: true,
        layers: false,
      },
    },
    
    import: {
      enabled: false,
    },
    workspaceControlPanel: {
      enabled: false,
    },
    selectedTheme: 'light',

    theme: {
      palette: {
        mode: "light",

        primary: {
          main: "#d70035",
        },
        secondary: {
          main: "#3E4955",
        },

        shades: {
          dark: "#F0F0F0",
          main: "#F0F0F0)",
          light: "#F0F0F0",
        },

        error: {
          main: "#b00020",
        },

        text: {
          primary: "#3E4955",
        },

        highlights: {
          primary: "rgba(250, 250, 250, 0)",
        },
      },

      typography: {
        fontFamily: '"robotomedium", sans-serif',

        button: {
          fontSize: "0.878rem",
          letterSpacing: "0.05rem",
          lineHeight: "2.25rem",
          textTransform: "uppercase",
        },
        buttonNext: {
          fontSize: "0.878rem",
          letterSpacing: "0.05rem",
          lineHeight: "2.25rem",
        },

        body1: {
          fontSize: "1rem",
          letterSpacing: "0em",
          lineHeight: "1.5em",
        },
        body1Next: {
          fontSize: "1rem",
          letterSpacing: "0em",
          lineHeight: "1.5em",
        },
        body2: {
          fontSize: "0.9rem",
          letterSpacing: "0.015em",
          lineHeight: "1.5em",
        },
        body2Next: {
          fontSize: "0.9rem",
          letterSpacing: "0.015em",
          lineHeight: "1.5em",
        },
      },

      components: {
        IIIFHtmlContent: {
          styleOverrides: {
            root: {
              "& a": {
                color: "#d70035",
                textDecoration: "underline",
              },
            },
          },
        },

        MuiTreeItem: {
          styleOverrides: {
            content: {
              borderBottom: "1px solid #000000",
              borderRadius: 0,
            },
          },
        },
      },
    },
  };
}