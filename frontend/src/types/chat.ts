
export interface MessagePart {
  type: string;
  text?: string;
  content?: string;
}

export interface Message {
  id?: string;
  role: 'user' | 'assistant' | 'tool';
  content?: string;
  parts?: MessagePart[];
  metadata?: {
    urls?: string[];
  };
}
