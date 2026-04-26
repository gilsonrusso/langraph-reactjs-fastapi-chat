import {
  Box,
  Stack,
  Typography,
  Avatar,
  TextField,
  IconButton,
  Paper,
  CircularProgress,
} from "@mui/material";
import SendIcon from "@mui/icons-material/Send";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import PersonIcon from "@mui/icons-material/Person";
import type { MessagePart as UIMessagePart } from "@tanstack/ai-client";
import { fetchServerSentEvents } from "@tanstack/ai-client";
import { type UIMessage, useChat } from "@tanstack/ai-react";
import React, { useEffect, useState } from "react";
import { useLocation } from "react-router";
import { chatService } from "../services/chatService";

interface ChatRouteProps {
  onHistoryUpdate?: () => void;
}

export const ChatRoute: React.FC<ChatRouteProps> = ({ onHistoryUpdate }) => {
  const [input, setInput] = useState("");
  const location = useLocation();
  const threadId = location.pathname.startsWith("/c/")
    ? location.pathname.split("/")[2]
    : null;

  const connection = React.useMemo(
    () =>
      fetchServerSentEvents("http://localhost:8000/api/chat", () => ({
        body: threadId ? { checkpoint_id: threadId } : {},
      })),
    [threadId],
  );

  const { messages, sendMessage, isLoading, setMessages } = useChat({
    connection,
  });

  useEffect(() => {
    if (threadId) {
      chatService
        .getChatHistory(threadId)
        .then((history) => {
          const uiMessages: UIMessage[] = history.map((msg) => ({
            id: msg.id,
            role:
              msg.role === "tool"
                ? "assistant"
                : (msg.role as "user" | "assistant" | "system"),
            parts: (msg.parts || []) as UIMessagePart[],
          }));
          setMessages(uiMessages);
        })
        .catch(() => setMessages([]));
    } else {
      setMessages([]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [threadId]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      sendMessage(input);
      setInput("");
      // Opcionalmente atualiza o histórico (ex: para refletir na sidebar)
      if (onHistoryUpdate) onHistoryUpdate();
    }
  };

  const renderInput = () => (
    <Paper
      component="form"
      onSubmit={handleSubmit}
      elevation={0}
      sx={{
        display: "flex",
        alignItems: "flex-end",
        width: "100%",
        maxWidth: "800px",
        p: "8px 16px",
        borderRadius: "32px",
        bgcolor: "background.paper",
        border: "1px solid",
        borderColor: "divider",
        minHeight: "56px",
      }}
    >
      <TextField
        fullWidth
        multiline
        maxRows={6}
        placeholder="Pergunte-me qualquer coisa!"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        disabled={isLoading}
        variant="standard"
        slotProps={{
          input: {
            disableUnderline: true,
            sx: {
              ml: 1,
              flex: 1,
              fontSize: "1rem",
              py: 1,
            },
          },
        }}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e as unknown as React.FormEvent);
          }
        }}
      />
      {isLoading && <CircularProgress size={24} sx={{ mx: 1, mb: 1.5 }} />}
      <IconButton
        type="submit"
        disabled={!input.trim() || isLoading}
        color="primary"
        sx={{ p: "12px", mb: 0.5 }}
      >
        <SendIcon />
      </IconButton>
    </Paper>
  );

  return (
    <Stack
      sx={{
        height: "100%",
        bgcolor: "background.default",
        color: "text.primary",
      }}
    >
      {messages.length === 0 ? (
        <Box
          sx={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            px: 2,
            mb: 10,
          }}
        >
          <Box sx={{ width: "100%", maxWidth: "800px", mb: 4 }}>
            <Typography variant="h3" sx={{ fontWeight: 500, mb: 1 }}>
              <span
                style={{
                  background:
                    "linear-gradient(90deg, #4285f4, #9b72cb, #d96570)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                }}
              >
                Olá!
              </span>
            </Typography>
            <Typography
              variant="h3"
              sx={{ color: "text.secondary", fontWeight: 500 }}
            >
              Por onde começamos?
            </Typography>
          </Box>
          {renderInput()}
        </Box>
      ) : (
        <>
          {/* Mensagens */}
          <Box
            sx={{
              flex: 1,
              overflowY: "auto",
              p: { xs: 2, md: 4 },
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
            }}
          >
            <Box
              sx={{
                width: "100%",
                maxWidth: "800px",
                display: "flex",
                flexDirection: "column",
                gap: 4,
              }}
            >
              {messages.map((message) => {
                const isAssistant = message.role === "assistant";
                return (
                  <Stack
                    key={message.id}
                    direction={isAssistant ? "row" : "row-reverse"}
                    spacing={2}
                    sx={{
                      alignSelf: isAssistant ? "flex-start" : "flex-end",
                      maxWidth: "90%",
                    }}
                  >
                    {isAssistant ? (
                      <Avatar
                        sx={{
                          bgcolor: "transparent",
                          color: "primary.main",
                          width: 36,
                          height: 36,
                          mt: 0.5,
                        }}
                      >
                        <AutoAwesomeIcon />
                      </Avatar>
                    ) : (
                      <Avatar
                        sx={{
                          bgcolor: "primary.main",
                          color: "white",
                          width: 36,
                          height: 36,
                          mt: 0.5,
                        }}
                      >
                        <PersonIcon />
                      </Avatar>
                    )}

                    <Box
                      sx={{
                        bgcolor: isAssistant
                          ? "transparent"
                          : "action.selected",
                        color: "text.primary",
                        p: 2,
                        borderRadius: "20px",
                      }}
                    >
                      {message.parts.map((part) => {
                        let partKey: string;
                        if ("toolCallId" in part) {
                          partKey = part.toolCallId;
                        } else if ("id" in part) {
                          partKey = part.id;
                        } else {
                          const contentSample =
                            "content" in part
                              ? part.content?.substring(0, 20)
                              : "";
                          partKey = `${message.id}-${part.type}-${contentSample}`;
                        }

                        if (part.type === "thinking") {
                          return (
                            <Typography
                              key={partKey}
                              variant="body2"
                              sx={{
                                color: "text.secondary",
                                fontStyle: "italic",
                                mb: 1,
                              }}
                            >
                              💭 Thinking: {part.content}
                            </Typography>
                          );
                        }
                        if (part.type === "tool-call") {
                          return (
                            <Typography
                              key={partKey}
                              variant="body2"
                              sx={{ color: "primary.main", mb: 1 }}
                            >
                              🛠️ Usando ferramenta: <strong>{part.name}</strong>
                              ...
                            </Typography>
                          );
                        }
                        if (part.type === "tool-result") {
                          return (
                            <Typography
                              key={partKey}
                              variant="body2"
                              sx={{ color: "success.main", mb: 1 }}
                            >
                              ✅ Ferramenta concluída.
                            </Typography>
                          );
                        }
                        if (part.type === "text") {
                          return (
                            <Typography
                              key={partKey}
                              variant="body1"
                              sx={{ whiteSpace: "pre-wrap" }}
                            >
                              {part.content}
                            </Typography>
                          );
                        }
                        return null;
                      })}
                    </Box>
                  </Stack>
                );
              })}
            </Box>
          </Box>

          {/* Input */}
          <Box
            sx={{
              p: 2,
              pb: 4,
              display: "flex",
              justifyContent: "center",
              bgcolor: "transparent",
            }}
          >
            {renderInput()}
          </Box>
        </>
      )}
    </Stack>
  );
};
