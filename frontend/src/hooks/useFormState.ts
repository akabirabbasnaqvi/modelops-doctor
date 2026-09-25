import { useCallback, useRef, useState } from "react";

/**
 * Shared controlled-form state.
 *
 * Replaces the `setFormData({ ...formData, field: value })` pattern that was
 * duplicated across the page components. Spreading the current object from
 * the closure reads a possibly stale value, so every update here goes through
 * the functional form of setState.
 */
export function useFormState<T extends object>(initialValues: T) {
  const [values, setValues] = useState<T>(initialValues);

  // Kept in a ref so reset() stays stable even if the caller passes a new
  // object literal on each render.
  const initialValuesRef = useRef(initialValues);

  const updateField = useCallback(
    <K extends keyof T>(field: K, value: T[K]) => {
      setValues((current) => ({ ...current, [field]: value }));
    },
    [],
  );

  const reset = useCallback(() => {
    setValues(initialValuesRef.current);
  }, []);

  return { values, setValues, updateField, reset };
}
