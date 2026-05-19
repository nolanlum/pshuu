import { afterEach, beforeEach, expect, test, vi } from 'vitest';

// frontend.jsx self-mounts on import and reads the `list_url` / `api_key`
// globals that manage.html normally emits, so set everything up first.
beforeEach(() => {
    document.body.innerHTML = '<div id="content"></div>';
    globalThis.list_url = '/list?k=testkey';
    globalThis.api_key = 'testkey';
    // jsdom has no IntersectionObserver; the hook may construct one.
    globalThis.IntersectionObserver = class {
        observe() {}
        unobserve() {}
        disconnect() {}
    };
    globalThis.fetch = vi.fn(() =>
        Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ status: 'pshuu~', files: {} }),
        })
    );
    vi.resetModules();
});

afterEach(() => {
    vi.restoreAllMocks();
    document.body.innerHTML = '';
});

test('initial DOM renders the manager shell and empty state', async () => {
    await import('./frontend.jsx');

    // Static shell + the empty state once the mocked /list resolves.
    await vi.waitFor(() => {
        const text = document.body.textContent;
        expect(text).toContain('pshuu');
        expect(document.querySelector('.manage-title')).not.toBeNull();
        expect(document.querySelector('.dropzone')).not.toBeNull();
        expect(text).toContain('drop files here');
        expect(text).toContain('no uploads yet');
    });

    // The list endpoint was hit with the api key from the template global.
    expect(globalThis.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/list?k=testkey')
    );
});
