document.addEventListener("DOMContentLoaded", function () {
  const chatPageContainer = document.getElementById(
    "chat-page-container",
  ) as HTMLElement;
  const chatOutput = document.getElementById(
    "chat-output",
  ) as HTMLDivElement | null;
  const historyMessagesContainer = document.getElementById(
    "history-messages",
  ) as HTMLDivElement | null;
  const messageInput = document.getElementById(
    "message-input",
  ) as HTMLInputElement | null;
  const sendButton = document.getElementById(
    "send-button",
  ) as HTMLButtonElement | null;
  const loadingIndicator = document.getElementById(
    "loading-indicator",
  ) as HTMLElement | null;
  const clearHistoryButton = document.getElementById(
    "clear-history-button",
  ) as HTMLButtonElement | null;
  const loadMoreSidebarButton = document.getElementById(
    "load-more-button-sidebar",
  ) as HTMLButtonElement | null;
  const noHistorySidebarMsg = document.getElementById(
    "no-history-sidebar-msg",
  ) as HTMLElement | null;
  const chatMainArea = document.getElementById(
    "chat-main-area",
  ) as HTMLElement | null;

  // Check if chatPageContainer exists before accessing its properties
  if (!chatPageContainer) {
    console.error("Chat page container not found");
    return;
  }

  // Define URLs and state variables
  const chatUrl: string = chatPageContainer.dataset.chatUrl || "";
  const loadMoreUrl: string = chatPageContainer.dataset.loadMoreUrl || "";
  const clearHistoryUrl: string =
    chatPageContainer.dataset.clearHistoryUrl || "";
  let currentOffsetForSidebar: number = parseInt(
    chatPageContainer.dataset.currentOffset || "0",
    10,
  );
  const initialLimit: number = parseInt(
    chatPageContainer.dataset.initialLimit || "10",
    10,
  );
  let totalMessagesInHistory: number = parseInt(
    chatPageContainer.dataset.totalMessages || "0",
    10,
  );

  let isLoadingMore: boolean = false;

  // --- Initial Setup ---
  function initializeChatView(): void {
    if (chatOutput) {
      chatOutput.scrollTop = chatOutput.scrollHeight;
    }
    if (historyMessagesContainer) {
      historyMessagesContainer.scrollTop = 0;
    }
  }
  initializeChatView();

  // --- Helper Functions ---
  function createMessageElement(
    messageText: string,
    sender: "user" | "agent",
  ): HTMLDivElement {
    const messageContainer = document.createElement("div");
    messageContainer.classList.add(
      sender === "user" ? "user-message" : "agent-message",
    );

    const messageBubble = document.createElement("div");
    messageBubble.classList.add("message-bubble");

    const messageSpan = document.createElement("span");
    messageSpan.innerHTML = messageText.replace(/\n/g, "<br>");

    messageBubble.appendChild(messageSpan);
    messageContainer.appendChild(messageBubble);
    return messageContainer;
  }

  function addMessageToLiveChat(
    messageText: string,
    sender: "user" | "agent",
  ): void {
    if (!chatOutput) return;
    const messageEl = createMessageElement(messageText, sender);
    chatOutput.appendChild(messageEl);
    chatOutput.scrollTop = chatOutput.scrollHeight;
    if (chatMainArea && chatMainArea.style.backgroundColor !== "transparent") {
      chatMainArea.style.backgroundColor = "#f8f9fa";
    }
  }

  function addMessageToHistorySidebar(
    messageText: string,
    sender: "user" | "agent",
    prepend: boolean = true,
  ): void {
    if (!historyMessagesContainer) return;
    const messageEl = createMessageElement(messageText, sender);

    if (prepend) {
      historyMessagesContainer.prepend(messageEl);
      historyMessagesContainer.scrollTop = 0;
    } else {
      historyMessagesContainer.appendChild(messageEl);
    }
    if (noHistorySidebarMsg && noHistorySidebarMsg.style.display !== "none") {
      noHistorySidebarMsg.style.display = "none";
    }
  }

  interface ChatResponse {
    response?: string;
    error?: string;
    success?: boolean;
    message?: string;
  }

  interface MessageData {
    message_text: string;
    sender: "user" | "agent";
  }

  interface LoadMoreResponse {
    messages: MessageData[];
    error?: string;
  }

  async function sendMessage(): Promise<void> {
    if (!messageInput) return;

    const messageText = messageInput.value.trim();
    if (!messageText) return;

    addMessageToLiveChat(messageText, "user");
    addMessageToHistorySidebar(messageText, "user", true);

    if (messageInput) messageInput.value = "";
    if (sendButton) sendButton.disabled = true;
    if (messageInput) messageInput.disabled = true;
    if (loadingIndicator) loadingIndicator.style.display = "block";

    try {
      if (!chatUrl) {
        throw new Error("Chat URL is not defined");
      }

      const response = await fetch(chatUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: messageText }),
      });

      let responseData: ChatResponse;
      try {
        responseData = await response.json();
      } catch (e) {
        const errorMsg = "Error: Could not parse server response.";
        addMessageToLiveChat(errorMsg, "agent");
        addMessageToHistorySidebar(errorMsg, "agent", true);
        console.error("Parsing error:", e);
        return;
      }

      if (!response.ok) {
        const errorMsg = responseData.error || `Error: ${response.statusText}`;
        addMessageToLiveChat(errorMsg, "agent");
        addMessageToHistorySidebar(errorMsg, "agent", true);
      } else if (responseData.response) {
        addMessageToLiveChat(responseData.response, "agent");
        addMessageToHistorySidebar(responseData.response, "agent", true);
      }
    } catch (error) {
      const networkErrorMsg = "Network error. Please try again.";
      addMessageToLiveChat(networkErrorMsg, "agent");
      addMessageToHistorySidebar(networkErrorMsg, "agent", true);
      console.error("Network/Fetch error:", error);
    } finally {
      if (sendButton) sendButton.disabled = false;
      if (messageInput) messageInput.disabled = false;
      if (loadingIndicator) loadingIndicator.style.display = "none";
      if (messageInput) messageInput.focus();
      totalMessagesInHistory += 2;
      currentOffsetForSidebar += 2;
    }
  }

  async function loadMoreSidebarMessages(): Promise<void> {
    if (isLoadingMore) return;
    isLoadingMore = true;

    if (loadingIndicator) loadingIndicator.style.display = "block";
    if (loadMoreSidebarButton) loadMoreSidebarButton.disabled = true;

    try {
      if (!loadMoreUrl) {
        throw new Error("Load more URL is not defined");
      }

      const response = await fetch(
        `${loadMoreUrl}?offset=${currentOffsetForSidebar}&limit=${initialLimit}`,
      );
      const data: LoadMoreResponse = await response.json();

      if (response.ok && data.messages) {
        data.messages.forEach((msg: MessageData) => {
          addMessageToHistorySidebar(msg.message_text, msg.sender, false);
        });
        currentOffsetForSidebar += data.messages.length;

        if (
          data.messages.length < initialLimit ||
          currentOffsetForSidebar >= totalMessagesInHistory
        ) {
          if (loadMoreSidebarButton)
            loadMoreSidebarButton.style.display = "none";
        }
      } else {
        console.error("Failed to load more messages for sidebar:", data.error);
      }
    } catch (error) {
      console.error("Error loading more sidebar messages:", error);
    } finally {
      isLoadingMore = false;
      if (loadingIndicator) loadingIndicator.style.display = "none";
      if (loadMoreSidebarButton) loadMoreSidebarButton.disabled = false;
    }
  }

  async function clearChatHistory(): Promise<void> {
    if (
      !confirm(
        "Are you sure you want to clear all chat history? This cannot be undone.",
      )
    ) {
      return;
    }

    try {
      if (!clearHistoryUrl) {
        throw new Error("Clear history URL is not defined");
      }

      const response = await fetch(clearHistoryUrl, { method: "POST" });
      const data: ChatResponse = await response.json();

      if (response.ok && data.success) {
        if (chatOutput) {
          const initialGreeting = chatOutput.querySelector(".initial-greeting");
          chatOutput.innerHTML = "";
          if (initialGreeting) chatOutput.appendChild(initialGreeting);
          chatOutput.scrollTop = chatOutput.scrollHeight;
        }

        if (historyMessagesContainer) {
          historyMessagesContainer.innerHTML = "";
          if (noHistorySidebarMsg) {
            historyMessagesContainer.appendChild(noHistorySidebarMsg);
            noHistorySidebarMsg.style.display = "block";
          }
        }

        currentOffsetForSidebar = 0;
        totalMessagesInHistory = 0;
        if (loadMoreSidebarButton) loadMoreSidebarButton.style.display = "none";
        alert(data.message || "Chat history cleared.");
      } else {
        alert(data.message || "Failed to clear chat history.");
      }
    } catch (error) {
      console.error("Error clearing chat history:", error);
      alert("An error occurred while clearing chat history.");
    }
  }

  // Event Listeners
  if (sendButton) sendButton.addEventListener("click", sendMessage);
  if (messageInput) {
    messageInput.addEventListener("keypress", (e: KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });
    messageInput.focus();
  }
  if (clearHistoryButton)
    clearHistoryButton.addEventListener("click", clearChatHistory);
  if (loadMoreSidebarButton)
    loadMoreSidebarButton.addEventListener("click", loadMoreSidebarMessages);
});
