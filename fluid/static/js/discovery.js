document.addEventListener("DOMContentLoaded", () => {
    const DISCOVERY = "ocean_discovery"
    const SUGGESTIONS = "ocean_discovery:suggestions"

    const STAGGER = 70
    const REQUEST_TIMEOUT = 12000

    const config = window.ocDiscovery || {}
    const events = new window.wf.ext.events.EventManager()

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

    function wait(ms) {
        return new Promise(resolve => setTimeout(resolve, ms))
    }

    async function request(query, data) {
        const result = await Promise.race([
            events.request(query, data),
            wait(REQUEST_TIMEOUT).then(() => Promise.reject("timeout"))
        ])
        if (!result) throw "unanswered"
        return result
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

    function filterPayload(payload) {
        const types = typeChecks.filter(c => c.checked && !c.disabled).map(c => c.value)
        if (types.length) payload.type = types.join(",")

        const licenses = licenseChecks.filter(c => c.checked && !c.disabled).map(c => c.value)
        if (licenses.length === 1) payload.license = licenses[0]

        const sort = sortRadios.find(r => r.checked && !r.disabled)
        if (sort && sort.value !== "newest") payload.sort = sort.value
        return payload
    }

    function payload() {
        const data = {}
        const q = search.value.trim()
        if (q) data.q = q
        return filterPayload(data)
    }

    function urlParams() {
        const params = new URLSearchParams()
        for (const [key, value] of Object.entries(payload())) params.set(key, value)
        return params
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

    // staggered reveal

    const pending = []
    const observer = new IntersectionObserver(onIntersect, { rootMargin: "120px 0px" })

    let ordinal = 0
    let revealing = false

    function onIntersect(entries) {
        let queued = false
        for (const entry of entries) {
            if (!entry.isIntersecting) continue
            observer.unobserve(entry.target)
            pending.push(entry.target)
            queued = true
        }
        if (queued) reveal()
    }

    async function reveal() {
        if (revealing) return
        revealing = true

        while (pending.length) {
            pending.sort((a, b) => Number(a.dataset.ord) - Number(b.dataset.ord))
            const card = pending.shift()
            if (!card.isConnected) continue

            card.classList.add("is-in")
            await wait(STAGGER)
        }

        revealing = false
    }

    function buildCard(html) {
        const holder = document.createElement("template")
        holder.innerHTML = html.trim()
        return holder.content.firstElementChild
    }

    function appendCards(cards) {
        for (const html of cards || []) {
            const card = buildCard(html)
            if (!card) continue

            card.dataset.ord = String(ordinal++)
            results.appendChild(card)
            resolveIcons(card)
            observer.observe(card)
        }
    }

    function clearCards() {
        observer.disconnect()
        pending.length = 0
        ordinal = 0
        results.replaceChildren()
    }

    function showNotice(icon, text) {
        const box = document.createElement("div")
        box.className = "oc-empty"

        const emoji = document.createElement("span")
        emoji.textContent = icon
        const message = document.createElement("p")
        message.textContent = text

        box.append(emoji, message)
        results.appendChild(box)
    }

    // slices

    let loading = false

    async function fetchSlice(offset, replace) {
        if (loading) return
        loading = true
        more.disabled = true

        try {
            const data = await request(DISCOVERY, { ...payload(), offset })

            if (replace) clearCards()
            appendCards(data.cards)

            if (data.empty) results.insertAdjacentHTML("beforeend", data.empty)
            more.dataset.offset = String(data.next_offset)
            more.hidden = !data.has_more
        } catch {
            if (!replace) return

            clearCards()
            showNotice("⚠️", config.i18n?.error || "")
            more.hidden = true
        } finally {
            loading = false
            more.disabled = false
        }
    }

    function applyResults() {
        const params = urlParams()
        history.pushState(null, "", params.toString() ? `/?${params}` : "/")
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

        const data = filterPayload({ q })
        delete data.sort

        try {
            const result = await request(SUGGESTIONS, data)
            renderSuggestions(result.suggestions || [])
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

    // initial state from URL

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

    results.classList.add("oc-grid-live")
    syncFromUrl()
    fetchSlice(0, true)

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
})
