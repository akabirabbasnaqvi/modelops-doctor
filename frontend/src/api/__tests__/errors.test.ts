import { describe, expect, it } from "vitest";

import { getErrorMessage } from "../errors";

const FALLBACK = "Something went wrong.";

function apiError(detail: unknown) {
  return { response: { data: { detail } } };
}

describe("getErrorMessage", () => {
  it("returns a string detail as-is", () => {
    expect(getErrorMessage(apiError("Project already exists."), FALLBACK)).toBe(
      "Project already exists.",
    );
  });

  it("joins the messages of a FastAPI validation error", () => {
    const detail = [
      {
        loc: ["body", "name"],
        msg: "String should have at most 150 characters",
        type: "string_too_long",
      },
      {
        loc: ["body", "version"],
        msg: "Field required",
        type: "missing",
      },
    ];

    expect(getErrorMessage(apiError(detail), FALLBACK)).toBe(
      "String should have at most 150 characters Field required",
    );
  });

  it("skips validation entries that have no message", () => {
    const detail = [{ loc: ["body"] }, { msg: "Field required" }, "stray"];

    expect(getErrorMessage(apiError(detail), FALLBACK)).toBe("Field required");
  });

  it("falls back when a validation array has no usable messages", () => {
    expect(getErrorMessage(apiError([{ loc: ["body"] }]), FALLBACK)).toBe(
      FALLBACK,
    );
  });

  it("falls back when the detail is an empty string", () => {
    expect(getErrorMessage(apiError("   "), FALLBACK)).toBe(FALLBACK);
  });

  it("falls back when the detail is some other object", () => {
    expect(getErrorMessage(apiError({ code: 500 }), FALLBACK)).toBe(FALLBACK);
  });

  it("falls back when there is no response, e.g. a network error", () => {
    expect(getErrorMessage(new Error("Network Error"), FALLBACK)).toBe(
      FALLBACK,
    );
  });

  it("falls back for non-object errors", () => {
    expect(getErrorMessage("boom", FALLBACK)).toBe(FALLBACK);
    expect(getErrorMessage(null, FALLBACK)).toBe(FALLBACK);
    expect(getErrorMessage(undefined, FALLBACK)).toBe(FALLBACK);
  });
});
