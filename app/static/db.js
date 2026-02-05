const DB = (function () {
    const apiBase = '/api';

    const request = async (path, options = {}) => {
        const response = await fetch(`${apiBase}${path}`, {
            headers: { 'Content-Type': 'application/json' },
            ...options
        });

        if (!response.ok) {
            let message = response.statusText;
            try {
                const data = await response.json();
                if (data && data.detail) message = data.detail;
            } catch (err) {
                // Ignore parse errors
            }
            throw new Error(message);
        }

        if (response.status === 204) return null;
        return response.json();
    };

    return {
        init: () => { },
        isConnected: () => true,
        requireConnection: () => true,

        async fetchSongs() {
            try {
                const data = await request('/songs');
                return { data, error: null };
            } catch (error) {
                return { data: null, error };
            }
        },

        async getSong(id, expandChoruses = false) {
            try {
                const flag = expandChoruses ? 'true' : 'false';
                const data = await request(`/songs/${id}?expand_choruses=${flag}`);
                return { data, error: null };
            } catch (error) {
                return { data: null, error };
            }
        },

        async saveSong(songId, title, content) {
            try {
                const payload = JSON.stringify({ title, content });
                const data = songId
                    ? await request(`/songs/${songId}/chords`, { method: 'PUT', body: payload })
                    : await request('/songs', { method: 'POST', body: payload });
                return { data, error: null };
            } catch (error) {
                return { data: null, error };
            }
        },

        async prepareLyrics(title, lyrics, existingContent, language) {
            try {
                const payload = JSON.stringify({
                    title,
                    lyrics,
                    existing_content: existingContent,
                    language
                });
                const data = await request('/lyrics/prepare', { method: 'POST', body: payload });
                return { data, error: null };
            } catch (error) {
                return { data: null, error };
            }
        },

        async previewChords(content, lineIndex, charIndex, chord, language) {
            try {
                const payload = JSON.stringify({
                    content,
                    line_index: lineIndex,
                    char_index: charIndex,
                    chord,
                    language
                });
                const data = await request('/chords/preview', { method: 'POST', body: payload });
                return { data, error: null };
            } catch (error) {
                return { data: null, error };
            }
        }
    };
})();
