import { memo, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import useScenarios from '@hooks/useScenarios'

const stateStyles = {
  idle: {
    bg: 'bg-surface-glass hover:bg-surface-glass-hover',
    text: 'text-text-secondary',
    border: 'border-white/10',
  },
  loading: {
    bg: 'bg-accent-purple/20',
    text: 'text-accent-purple',
    border: 'border-accent-purple/30',
  },
  active: {
    bg: 'bg-accent-cyan/20',
    text: 'text-accent-cyan',
    border: 'border-accent-cyan/30',
  },
  complete: {
    bg: 'bg-status-normal/20',
    text: 'text-status-normal',
    border: 'border-status-normal/30',
  },
}

const ScenarioButton = memo(({ scenario, state, onClick, disabled }) => {
  const styles = stateStyles[state] || stateStyles.idle

  return (
    <motion.button
      onClick={() => onClick(scenario.id)}
      disabled={disabled}
      className={`
        w-full p-3 rounded-glass border transition-all text-left
        ${styles.bg} ${styles.text} ${styles.border}
        ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
      `}
      whileHover={!disabled ? { scale: 1.02 } : {}}
      whileTap={!disabled ? { scale: 0.98 } : {}}
    >
      <div className="flex items-center gap-3">
        <div className="relative w-8 h-8 flex items-center justify-center shrink-0">
          {state === 'loading' && (
            <motion.div
              className="absolute inset-0 rounded-full border-2 border-accent-purple border-t-transparent"
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
            />
          )}
          {state === 'active' && (
            <motion.div
              className="absolute inset-0 rounded-full bg-accent-cyan/30"
              animate={{ scale: [1, 1.3, 1], opacity: [0.5, 0.2, 0.5] }}
              transition={{ duration: 1.5, repeat: Infinity }}
            />
          )}
          {state === 'complete' && (
            <motion.span
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
            </motion.span>
          )}
          {(state === 'idle' || state === 'loading') && (
            <span className="w-5 h-5">
              {scenario.icon === 'check' && <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
              {scenario.icon === 'database' && <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" /></svg>}
              {scenario.icon === 'bolt' && <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>}
              {scenario.icon === 'rewind' && <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12.066 11.2a1 1 0 000 1.6l5.334 4A1 1 0 0019 16V8a1 1 0 00-1.6-.8l-5.333 4zM4.066 11.2a1 1 0 000 1.6l5.334 4A1 1 0 0011 16V8a1 1 0 00-1.6-.8l-5.334 4z" /></svg>}
            </span>
          )}
        </div>

        <div className="flex-1 min-w-0">
          <p className="text-body font-medium truncate">{scenario.name}</p>
          <p className="text-caption text-text-muted truncate">{scenario.description}</p>
        </div>

        {state !== 'idle' && (
          <motion.span
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            className={`shrink-0 px-2 py-0.5 rounded-full text-xs font-medium capitalize ${styles.bg}`}
          >
            {state}
          </motion.span>
        )}
      </div>
    </motion.button>
  )
})

function DemoControlPanel() {
  const [isOpen, setIsOpen] = useState(false)
  const { scenarios, activeScenario, triggerScenario, stopScenario, getScenarioState } = useScenarios()

  return (
    <>
      <motion.button
        onClick={() => setIsOpen(!isOpen)}
        className={`
          fixed top-1/2 -translate-y-1/2 z-50
          transition-all duration-300
          ${isOpen ? 'right-[280px]' : 'right-0'}
        `}
        whileHover={{ x: isOpen ? 0 : -4 }}
      >
        <div className={`
          flex items-center gap-1 px-2 py-4 rounded-l-lg
          border border-r-0 border-white/10
          ${isOpen ? 'bg-accent-purple text-white' : 'bg-surface-glass-active text-text-primary hover:bg-surface-glass-hover'}
        `}>
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z" /></svg>
          <motion.span
            animate={{ rotate: isOpen ? 180 : 0 }}
            className="text-xs"
          >
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
          </motion.span>
        </div>
      </motion.button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed top-0 right-0 h-full w-[280px] z-40 bg-background-secondary border-l border-white/10 shadow-2xl flex flex-col"
          >
            <div className="p-4 border-b border-white/5">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-section font-medium text-text-primary flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z" /></svg>
                  Demo Control
                </h3>
                {activeScenario && (
                  <button
                    onClick={stopScenario}
                    className="px-2 py-1 text-xs rounded bg-status-critical/20 text-status-critical hover:bg-status-critical/30 transition-colors"
                  >
                    Stop
                  </button>
                )}
              </div>
              <p className="text-caption text-text-muted">
                Trigger simulated attack scenarios
              </p>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-2">
              {scenarios.map((scenario) => (
                <ScenarioButton
                  key={scenario.id}
                  scenario={scenario}
                  state={getScenarioState(scenario.id)}
                  onClick={triggerScenario}
                  disabled={activeScenario && activeScenario !== scenario.id}
                />
              ))}
            </div>

            <div className="p-4 border-t border-white/5">
              <p className="text-caption text-text-muted text-center">
                Mock endpoints • No real attacks
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}

export default memo(DemoControlPanel)
