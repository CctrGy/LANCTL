workspace "LANCTL" "Suite para descubrir, inventariar y administrar infraestructuras LAN" {
    model {
        operator = person "Operador" "Administra redes y dispositivos mediante LANCTL."

        lanctl = softwareSystem "LANCTL" "Suite CLI, TUI y GUI para infraestructura LAN." {
            launchers = container "Launchers" "LANCTL, LANIP, LANWIRE, LANRACK, LANACCESS y LANMON." "Python"
            core = container "Core" "Contratos, configuración, persistencia, proyectos, plugins y tareas." "Python"
            interfaces = container "Interfaces" "CLI, TUI y GUI que presentan los servicios de la suite." "Python, JavaScript"
            storage = container "Almacenamiento local" "Inventarios, proyectos VLF, configuración y auditoría." "JSON, SQLite, VLF"
            plugins = container "Plugins LCP" "Extensiones versionadas con permisos y contratos públicos." "LCP"

            operator -> interfaces "Utiliza"
            launchers -> interfaces "Inicia"
            interfaces -> core "Solicita operaciones"
            core -> storage "Lee y escribe mediante transacciones"
            core -> plugins "Carga contratos autorizados"
            plugins -> core "Usa la API pública versionada"
        }
    }

    views {
        systemContext lanctl "SystemContext" {
            include *
            autoLayout lr
        }
        container lanctl "Containers" {
            include *
            autoLayout lr
        }
        styles {
            element "Software System" {
                background #1769aa
                color #ffffff
            }
            element "Container" {
                background #243447
                color #ffffff
            }
            element "Person" {
                shape person
                background #45e0ce
                color #101820
            }
        }
    }
}
