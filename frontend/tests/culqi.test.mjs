import test from "node:test";
import assert from "node:assert/strict";
import { authenticate } from "../src/features/payments/culqi.ts";

function browser() {
  const target = new EventTarget();
  target.location = { origin: "http://127.0.0.1:5173" };
  target.setTimeout = setTimeout;
  target.Culqi3DS = { initAuthentication() {} };
  globalThis.window = target;
  return target;
}
function message(target, origin, data) {
  const event = new Event("message");
  Object.assign(event, { origin, data });
  target.dispatchEvent(event);
}

test("3DS ignores other origins and requires complete authentication parameters", async () => {
  const target = browser();
  let finished = false;
  const promise = authenticate("tkn_test_fixture").then(value => { finished = true; return value; });
  const parameters3DS = { eci: "05", xid: "x", cavv: "c", protocolVersion: "2.1.0" };
  message(target, "https://untrusted.example", { parameters3DS });
  message(target, target.location.origin, { parameters3DS: { eci: "05" } });
  await Promise.resolve();
  assert.equal(finished, false);
  message(target, target.location.origin, { parameters3DS });
  assert.deepEqual(await promise, parameters3DS);
});

test("leaving checkout aborts the authentication listener", async () => {
  const target = browser();
  const controller = new AbortController();
  const promise = authenticate("tkn_test_fixture", controller.signal);
  controller.abort();
  await assert.rejects(promise, /interrumpida/);
  message(target, target.location.origin, { parameters3DS: { eci: "05", xid: "x", cavv: "c", protocolVersion: "2.1.0" } });
});
