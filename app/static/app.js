const app = {
    state: {
        currentSongId: null,
        editingContent: null,
        currentLanguage: null,
        languageLocked: false,
        expandChoruses: false
    },

    router: {
        // Core navigation logic
        navigate: (viewId, params = {}, replace = false) => {
            console.log("Navigating to:", viewId, params);

            // Construct query string
            const urlParams = new URLSearchParams();
            if (viewId !== 'list') {
                urlParams.set('view', viewId);
            }

            Object.keys(params).forEach(key => {
                if (params[key]) urlParams.set(key, params[key]);
            });

            const scrollX = window.scrollX;
            const scrollY = window.scrollY;

            const queryString = urlParams.toString();
            // "List" view is default, so empty query string is also valid for it,
            // but we'll be explicit if needed or keep it clean.
            // Let's keep it clean: if view is list and no other params, empty string.
            const url = queryString ? `?${queryString}` : window.location.pathname;

            if (replace) {
                history.replaceState({ viewId, params, scrollX, scrollY }, '', url);
            } else {
                history.pushState({ viewId, params, scrollX, scrollY }, '', url);
            }

            app.router.loadView(viewId, params);
        },

        // Helper to perform the actual UI switch
        loadView: (viewId, params = {}) => {
            document.querySelectorAll('.view-section').forEach(el => el.classList.remove('active'));
            const view = document.getElementById(viewId + 'View');
            if (view) view.classList.add('active');

            if (viewId === 'list') {
                app.handlers.loadSongsList();
            } else if (viewId === 'song' && params.id) {
                // If we are navigating to song view, we need to load the song
                if (app.state.currentSongId !== params.id) {
                    app.handlers.viewSong(params.id, false); // false = don't navigate, just load
                } else {
                    // Even if same ID, we might need to re-render if we came from Edit
                    app.handlers.viewSong(params.id, false);
                }
            } else if (viewId === 'editor') {
                if (params.id) {
                    // Edit functionality
                    app.handlers.editCurrentSong(params.id, false);
                } else {
                    // New song
                    if (app.state.currentSongId !== null) {
                        // clear state if we were editing something
                        app.handlers.startNewSong(false);
                    }
                }
            }
        }
    },

    handlers: {
        init: () => {
            console.log("App initializing...");

            DB.init();

            // Bind Nav
            document.getElementById('navHome').onclick = () => app.router.navigate('list');
            document.getElementById('navAddSong').onclick = () => app.handlers.startNewSong();

            const chorusToggle = document.getElementById('expandChorusesToggle');
            if (chorusToggle) {
                chorusToggle.checked = app.state.expandChoruses;
                chorusToggle.onchange = () => {
                    app.state.expandChoruses = chorusToggle.checked;
                    if (app.state.currentSongId) {
                        app.handlers.viewSong(app.state.currentSongId, false);
                    }
                };
            }

            // Back/Forward button handler
            window.onpopstate = (event) => {
                if (event.state) {
                    app.router.loadView(event.state.viewId, event.state.params);
                } else {
                    app.handlers.handleInitialUrl();
                }
            };

            app.handlers.handleInitialUrl();
        },

        handleInitialUrl: () => {
            const urlParams = new URLSearchParams(window.location.search);
            const view = urlParams.get('view') || 'list';
            const id = urlParams.get('id');
            const params = {};
            if (id) params.id = id;
            history.replaceState({ viewId: view, params: params }, '', window.location.href);
            app.router.loadView(view, params);
        },

        loadSongsList: async () => {
            console.log("Loading songs list...");
            const container = document.getElementById('songsList');
            container.innerHTML = '<div style="padding:1rem">Loading...</div>';

            const { data, error } = await DB.fetchSongs();
            if (error) {
                console.error("Error fetching songs:", error);
                container.innerHTML = `<div style="padding:1rem; color:red">Error loading songs: ${error.message}</div>`;
                return;
            }

            container.innerHTML = '';
            if (!data || data.length === 0) {
                container.innerHTML = '<div style="padding:1rem">No songs found. Add one!</div>';
                return;
            }

            data.forEach(song => {
                const el = document.createElement('div');
                el.className = 'song-item';
                el.innerHTML = `<div class="song-title">${song.title}</div>`;
                el.onclick = () => app.router.navigate('song', { id: song.id });
                container.appendChild(el);
            });
        },

        startNewSong: (navigate = true) => {
            console.log("Starting new song");
            app.state.currentSongId = null;
            app.state.editingContent = null;
            app.state.currentLanguage = null;
            app.state.languageLocked = false;
            document.getElementById('songTitleInput').value = '';
            document.getElementById('songLyricsInput').value = '';
            document.getElementById('editorTitle').innerText = 'Add New Song';
            document.getElementById('editStep1').style.display = 'block';
            document.getElementById('editStep2').style.display = 'none';
            if (navigate) app.router.navigate('editor');
        },

        viewSong: async (id, navigate = true) => {
            console.log("Viewing song:", id);
            const { data, error } = await DB.getSong(id, app.state.expandChoruses);
            if (error) {
                console.error("Error loading song:", error);
                alert("Error loading song");
                return;
            }
            app.state.currentSongId = data.id;
            const chorusToggle = document.getElementById('expandChorusesToggle');
            if (chorusToggle) {
                chorusToggle.checked = app.state.expandChoruses;
            }
            document.getElementById('viewSongTitle').innerText = data.title;
            app.ui.renderSong(data.content, document.getElementById('viewSongContainer'), false);
            if (navigate) app.router.navigate('song', { id: id });
        },

        editCurrentSong: async (id = null, navigate = true) => {
            const targetId = id || app.state.currentSongId;
            if (!targetId) { console.error("No id"); return; }
            app.state.currentSongId = targetId;

            const { data, error } = await DB.getSong(targetId);
            if (error) { alert("Failed to load"); return; }

            document.getElementById('editorTitle').innerText = 'Edit Song';
            document.getElementById('songTitleInput').value = data.title;
            const lines = data.content.map(l => l.text);
            document.getElementById('songLyricsInput').value = lines.join('\n');
            const lyricsText = data.content.map(l => l.text).join('\n');
            const prepared = await DB.prepareLyrics(
                data.title,
                lyricsText,
                data.content,
                app.state.languageLocked ? app.state.currentLanguage : null
            );

            if (prepared.error) {
                console.warn("Failed to prepare lyrics for edit:", prepared.error);
                app.state.editingContent = data.content;
                if (!app.state.currentLanguage) {
                    app.state.currentLanguage = 'pl';
                }
            } else {
                app.state.editingContent = prepared.data.content;
                app.state.currentLanguage = prepared.data.language || app.state.currentLanguage || 'pl';
            }

            document.getElementById('editStep1').style.display = 'none';
            document.getElementById('editStep2').style.display = 'block';

            const container = document.getElementById('chordEditorContainer');
            if (app.state.currentLanguage) {
                app.ui.renderLanguageSelector(app.state.currentLanguage);
            }
            app.ui.renderSong(app.state.editingContent || data.content, container, true);

            if (navigate) app.router.navigate('editor', { id: targetId });
        },

        goToChordMode: async () => {
            console.log("Going to chord mode...");
            const title = document.getElementById('songTitleInput').value;
            const text = document.getElementById('songLyricsInput').value;
            if (!title.trim() || !text.trim()) { alert("Please enter title and lyrics."); return; }
            document.getElementById('editStep1').style.display = 'none';
            document.getElementById('editStep2').style.display = 'block';

            const { data, error } = await DB.prepareLyrics(
                title,
                text,
                app.state.editingContent,
                app.state.languageLocked ? app.state.currentLanguage : null
            );

            if (error) {
                alert("Failed to prepare lyrics: " + error.message);
                return;
            }

            app.state.editingContent = data.content;
            app.state.currentLanguage = data.language || app.state.currentLanguage || 'pl';

            const container = document.getElementById('chordEditorContainer');
            app.ui.renderLanguageSelector(app.state.currentLanguage);
            app.ui.renderSong(data.content, container, true);
        },

        changeLanguage: (lang) => {
            app.state.currentLanguage = lang;
            app.state.languageLocked = true;
            app.ui.renderLanguageSelector(lang);
            console.log("Language changed to:", lang);
        },

        backToLyrics: () => {
            const currentContent = app.ui.scrapeContentFromEditor();
            app.state.editingContent = currentContent;
            document.getElementById('editStep1').style.display = 'block';
            document.getElementById('editStep2').style.display = 'none';
        },

        saveSong: async () => {
            console.log("Saving song...");
            const title = document.getElementById('songTitleInput').value;
            const content = app.ui.scrapeContentFromEditor();

            const result = await DB.saveSong(app.state.currentSongId, title, content);
            if (result.error) {
                console.error("Error saving:", result.error);
                alert("Error saving: " + result.error.message);
            } else {
                console.log("Song saved success");
                if (result.data) {
                    app.state.currentSongId = result.data.id;
                    app.handlers.viewSong(result.data.id, true);
                } else {
                    app.router.navigate('list');
                }
            }
        },

        applyChordChange: async (lineIndex, charIndex, chordText) => {
            let content = app.ui.scrapeContentFromEditor();
            const line = content[lineIndex];
            if (!line) return;

            if (chordText) {
                if (!line.chords) line.chords = {};
                line.chords[charIndex] = { text: chordText, type: 'manual' };
            } else if (line.chords && line.chords[charIndex]) {
                delete line.chords[charIndex];
            }

            const { data, error } = await DB.previewChords(
                content,
                lineIndex,
                charIndex,
                chordText || null,
                app.state.currentLanguage || 'pl'
            );

            if (error) {
                alert("Failed to apply chord change: " + error.message);
                return;
            }

            app.state.editingContent = data.content;
            const container = document.getElementById('chordEditorContainer');
            app.ui.renderSong(data.content, container, true);
        },

        applyChordMove: async (originLine, originChar, targetLine, targetChar, chordText) => {
            let content = app.ui.scrapeContentFromEditor();
            if (!content[originLine]) return;

            if (content[originLine].chords && content[originLine].chords[originChar]) {
                delete content[originLine].chords[originChar];
            }

            const removal = await DB.previewChords(
                content,
                originLine,
                originChar,
                null,
                app.state.currentLanguage || 'pl'
            );

            if (removal.error) {
                alert("Failed to move chord: " + removal.error.message);
                return;
            }

            content = removal.data.content;
            if (!content[targetLine]) return;
            if (!content[targetLine].chords) content[targetLine].chords = {};
            content[targetLine].chords[targetChar] = { text: chordText, type: 'manual' };

            const addition = await DB.previewChords(
                content,
                targetLine,
                targetChar,
                chordText,
                app.state.currentLanguage || 'pl'
            );

            if (addition.error) {
                alert("Failed to move chord: " + addition.error.message);
                return;
            }

            app.state.editingContent = addition.data.content;
            const container = document.getElementById('chordEditorContainer');
            app.ui.renderSong(addition.data.content, container, true);
        },

        handleDragStart: (e) => {
            e.target.classList.add('dragging');
            e.dataTransfer.setData('text/plain', e.target.innerText);
            const wrapper = e.target.closest('.char-wrapper');
            e.dataTransfer.setData('origin-line', wrapper.dataset.lineIndex);
            e.dataTransfer.setData('origin-char', wrapper.dataset.charIndex);
        },

        handleDragEnd: (e) => {
            e.target.classList.remove('dragging');
            document.querySelectorAll('.char-wrapper').forEach(el => el.classList.remove('drag-over'));
        },

        handleDragOver: (e) => {
            e.preventDefault();
            const wrapper = e.target.closest('.char-wrapper');
            if (wrapper) wrapper.classList.add('drag-over');
        },

        handleDragLeave: (e) => {
            const wrapper = e.target.closest('.char-wrapper');
            if (wrapper) wrapper.classList.remove('drag-over');
        },

        handleDrop: async (e) => {
            e.preventDefault();
            const wrapper = e.target.closest('.char-wrapper');
            if (!wrapper) return;
            wrapper.classList.remove('drag-over');

            const chordText = e.dataTransfer.getData('text/plain');
            const originLine = parseInt(e.dataTransfer.getData('origin-line'));
            const originChar = parseInt(e.dataTransfer.getData('origin-char'));

            const targetLine = parseInt(wrapper.dataset.lineIndex);
            const targetChar = parseInt(wrapper.dataset.charIndex);

            await app.handlers.applyChordMove(originLine, originChar, targetLine, targetChar, chordText);
        }
    },

    ui: {
        renderSong: (content, container, isEditable) => {
            container.innerHTML = '';

            content.forEach((lineObj, lineIndex) => {
                const lineDiv = document.createElement('div');
                lineDiv.className = 'lyric-line';
                if (lineObj.section === 'chorus') {
                    lineDiv.classList.add('chorus-line');
                }
                lineDiv.dataset.lineIndex = lineIndex;

                const chars = lineObj.text.split('');
                const eolIndex = chars.length;
                const hasEolChord = lineObj.chords && lineObj.chords[eolIndex];
                const shouldRender = chars.length > 0 || isEditable || hasEolChord;

                if (!shouldRender) {
                    lineDiv.style.height = '1.5rem';
                    container.appendChild(lineDiv);
                    return;
                }

                if (lineObj.text.trim() === '') {
                    lineDiv.style.height = '1.5rem';
                }

                // Pre-calculate collisions
                const collidingIndices = new Set();
                if (lineObj.chords) {
                    const chordIndices = Object.keys(lineObj.chords)
                        .map(Number)
                        .sort((a, b) => a - b);

                    for (let i = 0; i < chordIndices.length - 1; i++) {
                        const currentIndex = chordIndices[i];
                        const currentChordData = lineObj.chords[currentIndex];
                        const currentChordText = typeof currentChordData === 'string' ? currentChordData : currentChordData.text;

                        const nextIndex = chordIndices[i + 1];

                        if (currentIndex + currentChordText.length >= nextIndex) {
                            collidingIndices.add(currentIndex);
                        }
                    }
                }

                const addWrapper = (char, charIndex, isEol = false) => {
                    const wrapper = document.createElement('div');
                    wrapper.className = 'char-wrapper';
                    if (char === ' ') wrapper.classList.add('is-space');
                    if (isEol) {
                        wrapper.classList.add('is-eol');
                        wrapper.dataset.eol = 'true';
                    }
                    if (collidingIndices.has(charIndex)) {
                        wrapper.classList.add('collision-detected');
                    }

                    wrapper.dataset.lineIndex = lineIndex;
                    wrapper.dataset.charIndex = charIndex;

                    const chordSpan = document.createElement('div');
                    chordSpan.className = 'chord';

                    // Check if chord exists
                    if (lineObj.chords && lineObj.chords[charIndex]) {
                        const cData = lineObj.chords[charIndex];
                        const cText = typeof cData === 'string' ? cData : cData.text;
                        const cType = typeof cData === 'string' ? 'manual' : (cData.type || 'manual');

                        chordSpan.innerText = cText;
                        if (cType === 'auto') chordSpan.classList.add('auto');

                        if (isEditable) {
                            chordSpan.draggable = true;
                            chordSpan.addEventListener('dragstart', app.handlers.handleDragStart);
                            chordSpan.addEventListener('dragend', app.handlers.handleDragEnd);
                        }
                    }

                    const letterSpan = document.createElement('div');
                    letterSpan.className = 'letter';
                    if (isEol) {
                        letterSpan.innerText = '\u00A0';
                    } else {
                        letterSpan.innerText = char === ' ' ? '\u00A0' : char;
                    }

                    wrapper.appendChild(chordSpan);
                    wrapper.appendChild(letterSpan);

                    if (isEditable) {
                        wrapper.onclick = (e) => {
                            e.stopPropagation();
                            const currentChordText = chordSpan.innerText;
                            app.ui.showChordInput(wrapper, currentChordText, async (newChord) => {
                                await app.handlers.applyChordChange(
                                    parseInt(wrapper.dataset.lineIndex),
                                    parseInt(wrapper.dataset.charIndex),
                                    newChord
                                );
                            });
                        };

                        wrapper.addEventListener('dragover', app.handlers.handleDragOver);
                        wrapper.addEventListener('dragleave', app.handlers.handleDragLeave);
                        wrapper.addEventListener('drop', app.handlers.handleDrop);
                    }

                    lineDiv.appendChild(wrapper);
                };

                chars.forEach((char, charIndex) => {
                    addWrapper(char, charIndex, false);
                });

                if (isEditable || hasEolChord) {
                    addWrapper(' ', eolIndex, true);
                }
                container.appendChild(lineDiv);
            });
        },

        renderLanguageSelector: (currentLang) => {
            const container = document.getElementById('languageSelectorContainer') || document.createElement('div');
            if (!container.id) {
                container.id = 'languageSelectorContainer';
                container.className = 'language-selector';
                const editorContainer = document.getElementById('chordEditorContainer');
                // Insert AFTER the editor container (under the lyrics)
                if (editorContainer.nextSibling) {
                    editorContainer.parentNode.insertBefore(container, editorContainer.nextSibling);
                } else {
                    editorContainer.parentNode.appendChild(container);
                }
            }

            const flags = {
                en: '🇺🇸 EN', pl: '🇵🇱 PL', de: '🇩🇪 DE', es: '🇪🇸 ES',
                fr: '🇫🇷 FR', pt: '🇵🇹 PT', ru: '🇷🇺 RU'
            };

            container.innerHTML = `
                <span class="lang-label">Language: </span>
                <span class="lang-current" onclick="app.ui.toggleLangMenu()">${flags[currentLang] || currentLang} ▼</span>
                <div class="lang-menu" style="display:none;">
                    ${Object.keys(flags).map(l =>
                `<div onclick="app.handlers.changeLanguage('${l}'); app.ui.toggleLangMenu()">${flags[l]}</div>`
            ).join('')}
                </div>
            `;
        },

        toggleLangMenu: () => {
            const menu = document.querySelector('.lang-menu');
            if (menu) menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
        },

        showChordInput: (targetWrapper, currentVal, onSave) => {
            const existing = document.querySelector('.chord-input-popup');
            if (existing) existing.remove();

            const popup = document.createElement('div');
            popup.className = 'chord-input-popup';

            const input = document.createElement('input');
            input.type = 'text';
            input.value = currentVal || '';
            input.placeholder = 'Chord';

            const saveBtn = document.createElement('button');
            saveBtn.innerText = '✓';

            const doSave = async () => {
                await onSave(input.value.trim());
                popup.remove();
            };

            saveBtn.onclick = () => { void doSave(); };

            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    void doSave();
                } else if (e.key === 'Escape') {
                    popup.remove();
                }
            });

            popup.appendChild(input);
            popup.appendChild(saveBtn);
            document.body.appendChild(popup);

            const rect = targetWrapper.getBoundingClientRect();
            popup.style.top = (rect.top + window.scrollY) + 'px';
            popup.style.left = (rect.left + window.scrollX + (rect.width / 2)) + 'px';

            input.focus();

            const closeHandler = (e) => {
                if (!popup.contains(e.target) && !targetWrapper.contains(e.target)) {
                    popup.remove();
                    document.removeEventListener('click', closeHandler);
                }
            };
            setTimeout(() => document.addEventListener('click', closeHandler), 0);
        },

        scrapeContentFromEditor: () => {
            const container = document.getElementById('chordEditorContainer');
            const lines = [];

            container.querySelectorAll('.lyric-line').forEach(lineDiv => {
                let text = "";
                let chords = {};

                lineDiv.querySelectorAll('.char-wrapper').forEach(wrapper => {
                    const isEol = wrapper.dataset.eol === 'true';
                    const letterSpan = wrapper.querySelector('.letter');
                    // Handle edge case where letterSpan might be missing if something broke, but shouldn't happen.
                    const char = letterSpan ? letterSpan.innerText : '';

                    const chordSpan = wrapper.querySelector('.chord');
                    const chordText = chordSpan ? chordSpan.innerText : '';
                    const isAuto = chordSpan ? chordSpan.classList.contains('auto') : false;

                    const index = parseInt(wrapper.dataset.charIndex);

                    if (!isEol) {
                        text += (char === '\u00A0' ? ' ' : char);
                    }
                    if (chordText && chordText.trim()) {
                        chords[index] = {
                            text: chordText.trim(),
                            type: isAuto ? 'auto' : 'manual'
                        };
                    }
                });

                lines.push({
                    text: text,
                    chords: chords,
                    section: lineDiv.classList.contains('chorus-line') ? 'chorus' : 'verse'
                });
            });

            return lines;
        }
    }
};

window.onload = app.handlers.init;
