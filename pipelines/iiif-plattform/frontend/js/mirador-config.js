export function createConfig({
  manifestId,
  canvasId = null,
  isCollection = false,
}) {

  const windowConfig = {
    manifestId: manifestId,
    thumbnailNavigationPosition: "off",
    view: "single",
  };

  if (canvasId) {
    windowConfig.canvasId = canvasId;
  }

  return {
    id: "my-mirador",
    language: "de",

    workspace: {
      allowNewWindows: true,
      draggingEnabled: true,
      showZoomControls: true,
      type: 'mosaic',
    },

    windows: [windowConfig],

    catalog: [
      { manifestId: manifestId }
    ],

    window: {
      allowClose: false,
      allowFullscreen: true,
      allowMaximize: false,
      allowTopMenuButton: false,
      allowWindowSideBar: true,
      sideBarPanel: 'canvas',
      defaultSidebarPanelHeight: 201,
      defaultSidebarPanelWidth: 235,
      defaultView: 'single',
      hideWindowTitle: true,
      highlightAllAnnotations: false,
      // Bei einer Sammlung (keine einzelne Abhandlung) zeigt der Index nur
      // eine nicht anklickbare Liste -- deshalb bleibt er dort zu; nur "Zeige
      // Sammlungen" funktioniert dort ohnehin als Navigation. Auf
      // Abhandlungsebene bleibt der Index (Inhaltsverzeichnis) wie gehabt an.
      sideBarOpen: !isCollection,
      showLocalePicker: true,
      switchCanvasOnSearch: true,

      panels: {
        info: false,
        attribution: false,
        canvas: !isCollection,
        annotations: false,
        search: false,
        layers: false,
      },

      views: [
        { key: 'single', behaviors: ['individuals'] },
        { key: 'book', behaviors: ['paged'] },
        { key: 'scroll', behaviors: ['continuous'] },
        { key: 'gallery' },
      ],
    },

    thumbnailNavigation: {
      defaultPosition: 'off',
      displaySettings: false,
      height: 100,
      showThumbnailLabels: true,
      width: 100,
    },

    osdConfig: {
      alwaysBlend: false,
      blendTime: 0.1,
      preserveImageSizeOnResize: true,
      showNavigationControl: false,
      zoomPerClick: 1,
      zoomPerDoubleClick: 2.0,
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

        // Default ist Gelb (#ffff00) -- markiert im Canvas-Index den
        // gerade sichtbaren/angeklickten Eintrag. Deaktiviert (echter
        // rgba-Farbwert noetig, das Keyword "transparent" kann MUIs
        // Farbfunktion nicht parsen und wirft einen Fehler).
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

        // Rahmen um die Eintraege im Canvas-Index (Inhaltsverzeichnis)
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