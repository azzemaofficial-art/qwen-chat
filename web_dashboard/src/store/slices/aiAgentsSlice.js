import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  agents: [],
  activeAgents: [],
  agentPerformance: {},
  consensusDecisions: [],
  agentStatus: {},
  loading: false,
  error: null,
};

const aiAgentsSlice = createSlice({
  name: 'aiAgents',
  initialState,
  reducers: {
    setAgents: (state, action) => {
      state.agents = action.payload;
      state.activeAgents = action.payload.filter(a => a.status === 'active');
    },
    updateAgentStatus: (state, action) => {
      const { agentId, status } = action.payload;
      const agent = state.agents.find(a => a.id === agentId);
      if (agent) {
        agent.status = status;
        state.activeAgents = state.agents.filter(a => a.status === 'active');
      }
    },
    updateAgentPerformance: (state, action) => {
      state.agentPerformance = action.payload;
    },
    addConsensusDecision: (state, action) => {
      state.consensusDecisions.unshift(action.payload);
    },
    setAgentStatus: (state, action) => {
      state.agentStatus = action.payload;
    },
    setLoading: (state, action) => {
      state.loading = action.payload;
    },
    setError: (state, action) => {
      state.error = action.payload;
    },
  },
});

export const {
  setAgents,
  updateAgentStatus,
  updateAgentPerformance,
  addConsensusDecision,
  setAgentStatus,
  setLoading,
  setError,
} = aiAgentsSlice.actions;

export default aiAgentsSlice.reducer;
