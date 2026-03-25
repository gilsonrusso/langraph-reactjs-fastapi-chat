
export interface MessagePart {
  type: string;
  text?: string;
  content?: string;
}

export type Role = 'user' | 'assistant' | 'tool';

export interface Message {
  id?: string;
  role: Role;
  content?: string;
  parts?: MessagePart[];
  metadata?: {
    urls?: string[];
  };
}
