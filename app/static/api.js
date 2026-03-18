async function request(url, options = {}) {
  const response = await fetch(url, options);
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const detail =
      payload && typeof payload === "object" && "detail" in payload
        ? payload.detail
        : `HTTP ${response.status}`;
    throw new Error(String(detail));
  }

  return payload;
}

export const api = {
  health() {
    return request("/api/health");
  },
  dashboard() {
    return request("/api/dashboard");
  },
  sampleTranscript() {
    return request("/api/demo/sample-transcript");
  },
  resetDemo() {
    return request("/api/demo/reset", { method: "POST" });
  },
  createMeeting(payload) {
    return request("/api/meetings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  },
  createMeetingFromAudio(formData) {
    return request("/api/meetings/from-audio", {
      method: "POST",
      body: formData,
    });
  },
  getMeeting(meetingId) {
    return request(`/api/meetings/${meetingId}`);
  },
  getTopicDetail(topicId) {
    return request(`/api/topics/${topicId}`);
  },
};
