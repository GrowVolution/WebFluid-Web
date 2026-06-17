document.addEventListener("DOMContentLoaded", () => {
    const API = "/hub/api/v1"

    const results = document.getElementById("ocResults")
    const more = document.getElementById("ocMore")
    const avatar = document.getElementById("ocAvatar")

    const search = document.getElementById("ocSearch")
    const suggestionsEl = document.getElementById("ocSuggestions")
    const filterToggle = document.getElementById("ocFilterToggle")
    const filterPanel = document.getElementById("ocFilterPanel")
    const applyBtn = document.getElementById("ocApply")

    const typeAll = document.getElementById("ocTypeAll")
    const licenseAll = document.getElementById("ocLicenseAll")
    const typeChecks = [...document.querySelectorAll(".oc-type")]
    const licenseChecks = [...document.querySelectorAll(".oc-license")]
    const sortRadios = [...document.querySelectorAll("input[name='ocSort']")]
    const priceSorts = sortRadios.filter(r => r.value === "price_asc" || r.value === "price_desc")

    const panel = document.getElementById("ocPanel")
    const panelText = document.getElementById("ocPanelText")
    const panelKey = document.getElementById("ocPanelKey")
    document.getElementById("ocPanelClose")?.addEventListener("click", () => panel.hidden = true)

    const authed = !!avatar

    function getCookie(name) {
        for (const cookie of document.cookie.split("; ")) {
            const [key, value] = cookie.split("=")
            if (key === name) return decodeURIComponent(value)
        }
        return null
    }

    function showPanel(text, key) {
        panelText.textContent = text
        if (panelKey) {
            panelKey.textContent = key || ""
            panelKey.hidden = !key
        }
        panel.hidden = false
    }

    function escapeHtml(value) {
        const div = document.createElement("div")
        div.textContent = value == null ? "" : String(value)
        return div.innerHTML
    }

    function emojiFor(type) {
        if (type === "additives") return "📦"
        if (type === "extensions") return "🧩"
        return "🎁"
    }

    function setDisabled(input, disabled) {
        input.disabled = disabled
        const label = input.closest(".oc-check")
        if (label) label.classList.toggle("is-disabled", disabled)
    }

    function onlyOpenSelected() {
        return licenseChecks.some(c => c.value === "open" && c.checked)
            && !licenseChecks.some(c => c.value === "paid" && c.checked)
    }

    function syncFilters() {
        const onlyOpen = onlyOpenSelected()

        typeChecks.forEach(check => {
            let disabled = typeAll.checked
            if (check.value === "extensions" && onlyOpen) disabled = true
            if (disabled) check.checked = false
            setDisabled(check, disabled)
        })

        licenseChecks.forEach(check => setDisabled(check, licenseAll.checked))

        priceSorts.forEach(radio => {
            setDisabled(radio, onlyOpen)
            if (onlyOpen && radio.checked) {
                radio.checked = false
                const newest = sortRadios.find(r => r.value === "newest")
                if (newest) newest.checked = true
            }
        })
    }

    typeAll.addEventListener("change", () => {
        if (typeAll.checked) typeChecks.forEach(c => c.checked = false)
        syncFilters()
    })
    licenseAll.addEventListener("change", () => {
        if (licenseAll.checked) licenseChecks.forEach(c => c.checked = false)
        syncFilters()
    })
    typeChecks.forEach(check => check.addEventListener("change", () => {
        typeAll.checked = !typeChecks.some(c => c.checked)
        syncFilters()
    }))
    licenseChecks.forEach(check => check.addEventListener("change", () => {
        licenseAll.checked = !licenseChecks.some(c => c.checked)
        syncFilters()
    }))

    function filterParams(query) {
        const types = typeChecks.filter(c => c.checked && !c.disabled).map(c => c.value)
        if (types.length) query.set("type", types.join(","))

        const licenses = licenseChecks.filter(c => c.checked && !c.disabled).map(c => c.value)
        if (licenses.length === 1) query.set("license", licenses[0])

        const sort = sortRadios.find(r => r.checked && !r.disabled)
        if (sort && sort.value !== "newest") query.set("sort", sort.value)
        return query
    }

    function params() {
        const query = new URLSearchParams()
        const q = search.value.trim()
        if (q) query.set("q", q)
        return filterParams(query)
    }

    function resolveIcons(scope) {
        scope.querySelectorAll("img[data-upload-id]").forEach(async (img) => {
            const id = img.dataset.uploadId
            if (!id || img.dataset.resolved) return
            img.dataset.resolved = "1"
            try {
                const res = await fetch(`/users/api/v1/upload/url?id=${encodeURIComponent(id)}`)
                if (!res.ok) return
                const data = await res.json()
                if (data && data.url) img.src = data.url
            } catch {}
        })
    }

    let loading = false

    async function fetchSlice(offset, replace) {
        if (loading) return
        loading = true
        more.disabled = true

        try {
            const query = params()
            query.set("offset", String(offset))
            const res = await fetch(`${API}/discovery?${query}`)
            if (!res.ok) return
            const data = await res.json()

            if (replace) results.innerHTML = data.html
            else results.insertAdjacentHTML("beforeend", data.html)

            resolveIcons(results)
            more.dataset.offset = String(data.next_offset)
            more.hidden = !data.has_more
        } finally {
            loading = false
            more.disabled = false
        }
    }

    function applyResults() {
        const query = params()
        history.pushState(null, "", query.toString() ? `/?${query}` : "/")
        fetchSlice(0, true)
    }

    // suggestions

    let activeIndex = -1

    function hideSuggestions() {
        suggestionsEl.hidden = true
        suggestionsEl.innerHTML = ""
        activeIndex = -1
    }

    function renderSuggestions(list) {
        if (!list.length) { hideSuggestions(); return }
        suggestionsEl.innerHTML = list.map(item => `
            <button type="button" class="oc-suggestion" data-id="${escapeHtml(item.id)}">
                <span class="oc-suggestion-emoji">${emojiFor(item.type)}</span>
                <span class="oc-suggestion-text">
                    <span class="oc-suggestion-name">${escapeHtml(item.name)}</span>
                    <span class="oc-suggestion-id">${escapeHtml(item.id)}</span>
                </span>
            </button>`).join("")
        suggestionsEl.hidden = false
        activeIndex = -1
    }

    async function fetchSuggestions() {
        const q = search.value.trim()
        if (!q) { hideSuggestions(); return }

        const query = new URLSearchParams()
        query.set("q", q)
        filterParams(query)
        query.delete("sort")

        try {
            const res = await fetch(`${API}/discovery/suggestions?${query}`)
            if (!res.ok) return
            const data = await res.json()
            renderSuggestions(data.suggestions || [])
        } catch {}
    }

    let debounce = null
    search.addEventListener("input", () => {
        if (debounce) clearTimeout(debounce)
        debounce = setTimeout(fetchSuggestions, 180)
    })

    function items() {
        return [...suggestionsEl.querySelectorAll(".oc-suggestion")]
    }

    function highlight(index) {
        const list = items()
        list.forEach((el, i) => el.classList.toggle("is-active", i === index))
        activeIndex = index
    }

    search.addEventListener("keydown", (e) => {
        const list = items()
        if (e.key === "ArrowDown" && !suggestionsEl.hidden) {
            e.preventDefault()
            highlight(Math.min(activeIndex + 1, list.length - 1))
        } else if (e.key === "ArrowUp" && !suggestionsEl.hidden) {
            e.preventDefault()
            highlight(Math.max(activeIndex - 1, 0))
        } else if (e.key === "Enter") {
            e.preventDefault()
            if (activeIndex >= 0 && list[activeIndex]) {
                search.value = list[activeIndex].dataset.id
            }
            hideSuggestions()
            applyResults()
        } else if (e.key === "Escape") {
            hideSuggestions()
        }
    })

    suggestionsEl.addEventListener("click", (e) => {
        const btn = e.target.closest(".oc-suggestion")
        if (!btn) return
        search.value = btn.dataset.id
        hideSuggestions()
        applyResults()
    })

    document.addEventListener("click", (e) => {
        if (!e.target.closest(".oc-search-wrap")) hideSuggestions()
    })

    // filter panel

    filterToggle?.addEventListener("click", () => {
        filterPanel.hidden = !filterPanel.hidden
    })
    applyBtn?.addEventListener("click", () => {
        filterPanel.hidden = true
        applyResults()
    })

    more?.addEventListener("click", () => {
        fetchSlice(parseInt(more.dataset.offset || "0", 10), false)
    })

    // initial state from URL + first paint icons

    function syncFromUrl() {
        const url = new URLSearchParams(window.location.search)
        if (url.has("q")) search.value = url.get("q")

        const types = (url.get("type") || "").split(",").filter(Boolean)
        if (types.length) {
            typeAll.checked = false
            typeChecks.forEach(c => c.checked = types.includes(c.value))
        }

        const license = url.get("license")
        if (license) {
            licenseAll.checked = false
            licenseChecks.forEach(c => c.checked = c.value === license)
        }

        const sort = url.get("sort")
        if (sort) {
            const radio = sortRadios.find(r => r.value === sort)
            if (radio) radio.checked = true
        }

        syncFilters()
    }

    syncFromUrl()
    resolveIcons(results)

    if (avatar) {
        fetch("/users/api/v1/profile/pp", { credentials: "include" })
            .then(res => res.ok ? res.json() : null)
            .then(data => {
                if (!data?.url) return
                const img = document.createElement("img")
                img.src = data.url
                img.alt = ""
                avatar.replaceChildren(img)
            })
            .catch(() => {})
    }

    const sessionId = new URLSearchParams(window.location.search).get("session_id")
    if (sessionId && authed) {
        history.replaceState(null, "", "/")
        fetch(`${API}/purchases/confirm`, {
            method: "POST",
            credentials: "include",
            headers: {
                "Content-Type": "application/json",
                "X-CSRF-Token": getCookie("csrf_token") || ""
            },
            body: JSON.stringify({ session_id: sessionId })
        })
            .then(res => res.ok ? res.json() : null)
            .then(data => {
                if (data?.status === "paid" && data?.key) {
                    showPanel("Payment complete! Your license key:", data.key)
                } else {
                    showPanel("Your payment has not been confirmed yet. Check back in a moment.")
                }
            })
            .catch(() => {})
    }
})
