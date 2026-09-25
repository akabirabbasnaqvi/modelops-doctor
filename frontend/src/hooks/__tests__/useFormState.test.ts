import { act, renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { useFormState } from "../useFormState";

type Form = {
  name: string;
  version: string;
  count: number;
  owner: string | null;
};

const initialValues: Form = {
  name: "",
  version: "1.0.0",
  count: 0,
  owner: null,
};

describe("useFormState", () => {
  it("starts with the supplied values", () => {
    const { result } = renderHook(() => useFormState(initialValues));

    expect(result.current.values).toEqual(initialValues);
  });

  it("updates a single field and leaves the rest untouched", () => {
    const { result } = renderHook(() => useFormState(initialValues));

    act(() => {
      result.current.updateField("name", "Churn Classifier");
    });

    expect(result.current.values.name).toBe("Churn Classifier");
    expect(result.current.values.version).toBe("1.0.0");
    expect(result.current.values.count).toBe(0);
  });

  it("applies consecutive updates within one batch", () => {
    const { result } = renderHook(() => useFormState(initialValues));

    act(() => {
      result.current.updateField("name", "First");
      result.current.updateField("version", "2.0.0");
    });

    expect(result.current.values).toEqual({
      ...initialValues,
      name: "First",
      version: "2.0.0",
    });
  });

  it("accepts non-string field values", () => {
    const { result } = renderHook(() => useFormState(initialValues));

    act(() => {
      result.current.updateField("count", 7);
      result.current.updateField("owner", null);
    });

    expect(result.current.values.count).toBe(7);
    expect(result.current.values.owner).toBeNull();
  });

  it("supports a functional update through setValues", () => {
    const { result } = renderHook(() => useFormState(initialValues));

    act(() => {
      result.current.setValues((current) => ({
        ...current,
        count: current.count + 5,
      }));
    });

    expect(result.current.values.count).toBe(5);
  });

  it("restores the original values on reset", () => {
    const { result } = renderHook(() => useFormState(initialValues));

    act(() => {
      result.current.updateField("name", "Changed");
      result.current.updateField("count", 9);
    });

    act(() => {
      result.current.reset();
    });

    expect(result.current.values).toEqual(initialValues);
  });

  it("does not mutate the caller's initial object", () => {
    const original = { ...initialValues };
    const { result } = renderHook(() => useFormState(initialValues));

    act(() => {
      result.current.updateField("name", "Mutated?");
    });

    expect(initialValues).toEqual(original);
  });

  it("keeps updateField and reset stable across renders", () => {
    const { result, rerender } = renderHook(() => useFormState(initialValues));

    const firstUpdate = result.current.updateField;
    const firstReset = result.current.reset;

    rerender();

    expect(result.current.updateField).toBe(firstUpdate);
    expect(result.current.reset).toBe(firstReset);
  });
});
