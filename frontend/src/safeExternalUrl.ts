export function safeExternalUrl(value: string | null | undefined): string | undefined {
  if (!value) return undefined;
  try {
    const url = new URL(value);
    const hasApiKey = [...url.searchParams.keys()].some((key) => key.toLowerCase() === "api_key");
    if (
      (url.protocol === "https:" || url.protocol === "http:") &&
      !url.username &&
      !url.password &&
      !hasApiKey
    ) {
      return url.href;
    }
  } catch {
    return undefined;
  }
}
