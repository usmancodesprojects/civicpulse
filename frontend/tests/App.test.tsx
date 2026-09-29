import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { App } from "../src/App";

const complaint = {
  id: "12345678-1234-1234-1234-123456789abc",
  text: "Water main is flooding the street",
  location: "Street 12",
  reporter_contact: null,
  category: "water",
  priority: "high",
  status: "open",
  ai_summary: "Burst water main flooding Street 12",
  triaged_by: "simulated",
  triage_latency_ms: 7,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
  allowed_transitions: ["in_progress", "rejected"],
};

describe("CivicPulse", () => {
  it("validates a short complaint before calling the API", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch");
    render(<App />);
    await userEvent.type(screen.getByLabelText("What happened?"), "short");
    await userEvent.type(screen.getByLabelText("Location"), "Street 1");
    await userEvent.click(screen.getByRole("button", { name: "Submit complaint" }));
    expect(screen.getByRole("alert")).toHaveTextContent("between 10 and 2000");
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("rejects an overlong contact before submission", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch");
    render(<App />);
    fireEvent.change(screen.getByLabelText("What happened?"), { target: { value: complaint.text } });
    fireEvent.change(screen.getByLabelText("Location"), { target: { value: complaint.location } });
    fireEvent.change(screen.getByLabelText("Contact (optional)"), { target: { value: "x".repeat(201) } });
    await userEvent.click(screen.getByRole("button", { name: "Submit complaint" }));
    expect(screen.getByRole("alert")).toHaveTextContent("200 characters or fewer");
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("renders category, priority, summary, and provider after submission", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify(complaint), { status: 201, headers: { "Content-Type": "application/json" } }));
    render(<App />);
    await userEvent.type(screen.getByLabelText("What happened?"), complaint.text);
    await userEvent.type(screen.getByLabelText("Location"), complaint.location);
    await userEvent.click(screen.getByRole("button", { name: "Submit complaint" }));
    expect(await screen.findByText(complaint.ai_summary)).toBeInTheDocument();
    expect(screen.getByText("water")).toBeInTheDocument();
    expect(screen.getByText("high")).toBeInTheDocument();
    expect(screen.getByText("simulated")).toBeInTheDocument();
  });

  it("clears an old triage result before validating a new report", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify(complaint), { status: 201 }));
    render(<App />);
    const description = screen.getByLabelText("What happened?");
    await userEvent.type(description, complaint.text);
    await userEvent.type(screen.getByLabelText("Location"), complaint.location);
    await userEvent.click(screen.getByRole("button", { name: "Submit complaint" }));
    expect(await screen.findByText(complaint.ai_summary)).toBeInTheDocument();

    await userEvent.clear(description);
    await userEvent.type(description, "short");
    await userEvent.click(screen.getByRole("button", { name: "Submit complaint" }));
    expect(screen.getByRole("alert")).toHaveTextContent("between 10 and 2000");
    expect(screen.queryByText(complaint.ai_summary)).not.toBeInTheDocument();
    expect(globalThis.fetch).toHaveBeenCalledTimes(1);
  });

  it("shows an honest loading message", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(() => new Promise(() => undefined));
    render(<App />);
    fireEvent.change(screen.getByLabelText("What happened?"), { target: { value: complaint.text } });
    fireEvent.change(screen.getByLabelText("Location"), { target: { value: complaint.location } });
    fireEvent.click(screen.getByRole("button", { name: "Submit complaint" }));
    expect(screen.getByRole("button", { name: /this may take a few seconds/i })).toBeDisabled();
  });

  it("loads dashboard complaints and server-provided transitions", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({ items: [complaint], total: 1, page: 1, page_size: 10 }), { status: 200, headers: { "Content-Type": "application/json" } }));
    render(<App />);
    await userEvent.click(screen.getByRole("button", { name: "Dashboard" }));
    expect(await screen.findByText(complaint.ai_summary)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Mark in progress" })).toBeInTheDocument();
  });

  it("keeps the newest dashboard filter result when an older request finishes later", async () => {
    let finishFirst: (response: Response) => void = () => undefined;
    const firstRequest = new Promise<Response>((resolve) => { finishFirst = resolve; });
    const fetchMock = vi.spyOn(globalThis, "fetch");
    fetchMock.mockReturnValueOnce(firstRequest);
    fetchMock.mockResolvedValueOnce(new Response(JSON.stringify({ items: [], total: 0, page: 1, page_size: 10 }), { status: 200 }));
    render(<App />);
    await userEvent.click(screen.getByRole("button", { name: "Dashboard" }));
    await userEvent.selectOptions(screen.getByLabelText("Filter by category"), "roads");
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    expect(screen.queryByText(complaint.ai_summary)).not.toBeInTheDocument();

    await act(async () => {
      finishFirst(new Response(JSON.stringify({ items: [complaint], total: 1, page: 1, page_size: 10 }), { status: 200 }));
      await firstRequest;
    });
    expect(screen.getByText("0 reports")).toBeInTheDocument();
    expect(screen.queryByText(complaint.ai_summary)).not.toBeInTheDocument();
  });

  it("surfaces the server 409 message verbatim", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch");
    fetchMock.mockResolvedValueOnce(new Response(JSON.stringify({ items: [complaint], total: 1, page: 1, page_size: 10 }), { status: 200, headers: { "Content-Type": "application/json" } }));
    fetchMock.mockResolvedValueOnce(new Response(JSON.stringify({ detail: "Invalid status transition: open -> resolved" }), { status: 409, headers: { "Content-Type": "application/json" } }));
    render(<App />);
    await userEvent.click(screen.getByRole("button", { name: "Dashboard" }));
    await userEvent.click(await screen.findByRole("button", { name: "Mark in progress" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Invalid status transition: open -> resolved");
  });

  it("renders stats and the X-Cache header", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({ by_category: { water: 4 }, by_priority: { high: 2 }, total: 4 }), { status: 200, headers: { "Content-Type": "application/json", "X-Cache": "HIT" } }));
    render(<App />);
    await userEvent.click(screen.getByRole("button", { name: "Stats" }));
    await waitFor(() => expect(screen.getByText("Cache HIT")).toBeInTheDocument());
    expect(screen.getByText("Total complaints")).toBeInTheDocument();
  });
});
