import { histogramLogic } from './histogramLogic'
import { initKeaTestLogic } from '~/test/init'
import { getConfig } from 'scenes/insights/Histogram/histogramUtils'
import { FunnelLayout } from 'lib/constants'

describe('histogramLogic', () => {
    let logic: ReturnType<typeof histogramLogic.build>

    initKeaTestLogic({
        logic: histogramLogic,
        onLogic: (l) => (logic = l),
    })

    describe('values', () => {
        it('has proper defaults', () => {
            expect(logic.values).toMatchSnapshot()
        })
    })

    describe('reducers', () => {
        describe('config', () => {
            it('is set via setConfig', async () => {
                const newConfig = getConfig(FunnelLayout.vertical, 1000, 3000)
                expect(logic.values.config).toEqual(getConfig(FunnelLayout.vertical))
                logic.actions.setConfig(newConfig)
                expect(logic.values.config).toEqual(newConfig)
            })
        })
    })
})
