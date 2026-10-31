import {defineConfig, loadConfigFromFile, mergeConfig} from "vite"
import fs from "fs"
import path from "path"

const WATCHED = new Set(["fluid", "additives"])
const SKIPPED = /(^|[\\/])(node_modules|dist|build|\.dart_tool|__pycache__|\.git)([\\/]|$)/
const CONFIGS = /\.(js|ts|mjs|cjs|json)$/

async function loadConfigs(command) {
    const additivesDir = path.resolve(__dirname, "additives")
    const configs = []

    for (const name of fs.readdirSync(additivesDir)) {
        let configPath = path.join(additivesDir, name, "frontend", "vite.config.ts")

        if (!fs.existsSync(configPath))
            configPath = path.join(additivesDir, name, "frontend", "vite.config.js")
        if (!fs.existsSync(configPath)) continue

        const loaded = await loadConfigFromFile(
            { command, mode: "development" },
            configPath
        )

        if (loaded?.config) configs.push(loaded.config)
    }

    let fluidConfig = path.resolve(__dirname, "fluid", "frontend", "vite.config.ts")
    if (!fs.existsSync(fluidConfig))
        fluidConfig = path.resolve(__dirname, "fluid", "frontend", "vite.config.js")
    if (fs.existsSync(fluidConfig)) {
        const loaded = await loadConfigFromFile(
            { command, mode: "development" },
            fluidConfig
        )
        if (loaded?.config) configs.push(loaded.config)
    }

    return configs
}

function mergeConfigs(configs) {
    let merged = {}

    for (const config of configs)
        merged = mergeConfig(merged, config)

    if (merged.plugins) {
        const seen = new Set()

        const updatedPlugins = []

        merged.plugins.forEach(plugin => {
            if (!Array.isArray(plugin)) {
                const key = plugin?.name || plugin
                if (seen.has(key)) return
                seen.add(key)
                updatedPlugins.push(plugin)
                return
            }

            const updatedPlugin = []

            for (const conf of plugin) {
                const name = conf?.name || conf
                if (seen.has(name)) continue
                seen.add(name)
                updatedPlugin.push(conf)
            }

            if (updatedPlugin.length === 0) return
            updatedPlugins.push(updatedPlugin)
        })

        merged.plugins = updatedPlugins
    }

    return merged
}

function unwatched(file) {
    const relative = path.relative(__dirname, file)
    if (!relative || relative.startsWith("..") || path.isAbsolute(relative)) return false
    if (SKIPPED.test(relative)) return true

    const parts = relative.split(/[\\/]/)
    if (parts.length === 1) return !WATCHED.has(parts[0]) && !CONFIGS.test(parts[0])
    if (parts[0] === "additives") return parts.length > 2 && parts[2] !== "frontend"
    return parts[0] !== "fluid"
}

function wfDevPlugin() {

    const namespaceRegex = /(fluid\/frontend|additives\/[^/]+\/frontend)/

    return {

        name: "wf-dev-plugin",
        enforce: "pre",

        configureServer(server) {
            server.watcher.on("error", error => {
                server.config.logger.warn(`[wf] Watching ${error?.path ?? "a file"} failed: ${error?.code ?? error}`)
            })
        },

        resolveId(id, importer) {

            if (!id.startsWith("/")) return null

            if (
                id.startsWith("/@") ||
                id.startsWith("/node_modules")
            ) {
                return null
            }

            if (!importer) return null

            const match = importer.match(namespaceRegex)
            if (!match) return null

            const namespace = match[1]
            const projectRoot = process.cwd()

            const asset = id.slice(1)

            const publicPath = path.resolve(
                projectRoot,
                namespace,
                "public",
                asset
            )

            if (fs.existsSync(publicPath)) return publicPath

            const normalPath = path.resolve(
                projectRoot,
                namespace,
                asset
            )

            if (fs.existsSync(normalPath)) return normalPath

            return null
        },
    }
}

export default defineConfig(async ({ command }) => {
    const configs = await loadConfigs(command)

    let config = {
        server: {
            fs: {
                allow: ["."]
            },
            watch: {
                ignored: [unwatched]
            }
        },
        plugins: []
    }
    configs.push(config)

    config = mergeConfigs(configs)
    config.plugins.push(wfDevPlugin())

    return config
})