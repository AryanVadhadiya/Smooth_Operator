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
              className="text-lg"
            >
              ✓
            </motion.span>
          )}
          {(state === 'idle' || state === 'loading') && (
            <span className="text-xl">{scenario.icon}</span>
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
          <span className="text-lg">🎮</span>
          <motion.span
            animate={{ rotate: isOpen ? 180 : 0 }}
            className="text-xs"
          >
            ◀
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
                  <span>🎮</span>
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
