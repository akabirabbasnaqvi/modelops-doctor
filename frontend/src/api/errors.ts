/**
 * Turn an API error into a message that is safe to render.
 *
 * FastAPI returns `detail` in two shapes:
 * - a string, for errors raised with HTTPException
 * - an array of `{ loc, msg, type }` objects, for request validation errors (422)
 *
 * Rendering the array directly throws "Objects are not valid as a React child",
 * so every page should go through this helper instead of reading `detail` itself.
 */
export function getErrorMessage(error: unknown, fallback: string): string {
  const detail = readDetail(error);

  if (typeof detail === "string" && detail.trim() !== "") {
    return detail;
  }

  if (Array.isArray(detail)) {
    const messages = detail
      .map((issue) =>
        isRecord(issue) && typeof issue.msg === "string" ? issue.msg : null,
      )
      .filter((message): message is string => message !== null);

    if (messages.length > 0) {
      return messages.join(" ");
    }
  }

  return fallback;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function readDetail(error: unknown): unknown {
  if (!isRecord(error)) {
    return undefined;
  }

  const response = error.response;

  if (!isRecord(response)) {
    return undefined;
  }

  const data = response.data;

  if (!isRecord(data)) {
    return undefined;
  }

  return data.detail;
}
