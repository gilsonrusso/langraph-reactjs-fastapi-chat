import React from 'react';
import { Box, Card, Typography, Button, Stack, Divider } from '@mui/material';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import BlockIcon from '@mui/icons-material/Block';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';

export interface ActionRequest {
  name: string;
  args: Record<string, any>;
  description: string;
}

export interface HITLRequest {
  action_requests: ActionRequest[];
}

export interface ApprovalCardProps {
  hitlRequest: HITLRequest;
  onDecision: (decision: { type: string; message?: string }) => void;
  isLoading?: boolean;
}

const ApprovalCard: React.FC<ApprovalCardProps> = ({ hitlRequest, onDecision, isLoading }) => {
  const request = hitlRequest.action_requests[0]; // Simplificado para o primeiro pedido
  if (!request) return null;

  return (
    <Card 
      variant="outlined" 
      sx={{ 
        p: 2, 
        my: 2, 
        borderRadius: 2, 
        borderLeft: '4px solid #f59e0b',
        bgcolor: 'rgba(245, 158, 11, 0.05)',
        maxWidth: 500
      }}
    >
      <Stack spacing={2}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <InfoOutlinedIcon color="warning" />
          <Typography variant="subtitle1" fontWeight="bold">
            Ação Requer Aprovação
          </Typography>
        </Box>

        <Typography variant="body2" color="text.secondary">
          {request.description}
        </Typography>

        <Box sx={{ bgcolor: 'rgba(0,0,0,0.03)', p: 1.5, borderRadius: 1, fontSize: '0.85rem' }}>
          <Typography variant="caption" fontWeight="bold" display="block" mb={1} color="text.secondary">
            DETALHES DA CHAMADA:
          </Typography>
          <Box component="pre" sx={{ m: 0, overflowX: 'auto', whiteSpace: 'pre-wrap' }}>
            {JSON.stringify(request.args, null, 2)}
          </Box>
        </Box>

        <Divider />

        <Stack direction="row" spacing={2} justifyContent="flex-end">
          <Button 
            variant="outlined" 
            color="error" 
            startIcon={<BlockIcon />}
            onClick={() => onDecision({ type: 'reject', message: 'User rejected the action.' })}
            disabled={isLoading}
          >
            Rejeitar
          </Button>
          <Button 
            variant="contained" 
            color="warning" 
            startIcon={<CheckCircleOutlineIcon />}
            onClick={() => onDecision({ type: 'approve' })}
            disabled={isLoading}
          >
            Aprovar
          </Button>
        </Stack>
      </Stack>
    </Card>
  );
};

export default ApprovalCard;
