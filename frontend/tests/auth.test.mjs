import test from 'node:test';
import assert from 'node:assert/strict';
import { getSession, login, logout, checkArea, AuthError } from '../src/features/auth/authApi.ts';

test('session distinguishes anonymous users from server/network failures', async (t) => {
  const fetchMock = t.mock.method(globalThis, 'fetch');
  fetchMock.mock.mockImplementation(async () => new Response('{}', { status: 403 }));
  assert.equal(await getSession(), null);
  fetchMock.mock.mockImplementation(async () => new Response('{}', { status: 500 }));
  await assert.rejects(getSession(), error => error instanceof AuthError && error.status === 500);
  fetchMock.mock.mockImplementation(async () => { throw new TypeError('offline'); });
  await assert.rejects(getSession(), /offline/);
});

test('login and logout fetch fresh CSRF tokens and never put passwords in URLs', async (t) => {
  const calls = [];
  const user = { id: 1, username: 'cook', roles: ['KITCHEN'], permissions: ['accounts.access_kitchen'] };
  t.mock.method(globalThis, 'fetch', async (url, init) => {
    calls.push({ url, init });
    return Response.json(url.endsWith('csrf/') ? { csrfToken: `token-${calls.length}` } : { user });
  });
  assert.deepEqual(await login('cook', 'secret'), user);
  await logout();
  assert.equal(calls[1].init.headers['X-CSRFToken'], 'token-1');
  assert.equal(calls[3].init.headers['X-CSRFToken'], 'token-3');
  assert.equal(calls[1].init.credentials, 'same-origin');
  assert.equal(calls[1].init.cache, 'no-store');
  assert.equal(JSON.parse(calls[1].init.body).password, 'secret');
  assert.ok(calls.every(call => !call.url.includes('secret')));
});

test('area authorization failures remain failures', async (t) => {
  t.mock.method(globalThis, 'fetch', async () => Response.json({ detail: 'Denied' }, { status: 403 }));
  await assert.rejects(checkArea('bar', new AbortController().signal), /Denied/);
});
