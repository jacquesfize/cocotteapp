import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it } from 'vitest'
import Pagination from '../../src/components/Pagination.vue'
import { i18n } from '../../src/i18n'

function mountPagination(props) {
  return mount(Pagination, {
    props,
    global: { plugins: [i18n] },
  })
}

beforeEach(() => {
  i18n.global.locale.value = 'fr'
})

describe('Pagination', () => {
  it('renders nothing when everything fits on one page', () => {
    const wrapper = mountPagination({ page: 1, count: 12, pageSize: 20 })

    expect(wrapper.find('.pagination').exists()).toBe(false)
  })

  it('shows the current page and total, and disables the previous button on the first page', () => {
    const wrapper = mountPagination({ page: 1, count: 45, pageSize: 20 })

    expect(wrapper.text()).toContain('Page 1 / 3')
    const [previous, next] = wrapper.findAll('button')
    expect(previous.attributes('disabled')).toBeDefined()
    expect(next.attributes('disabled')).toBeUndefined()
  })

  it('disables the next button on the last page', () => {
    const wrapper = mountPagination({ page: 3, count: 45, pageSize: 20 })

    const [previous, next] = wrapper.findAll('button')
    expect(previous.attributes('disabled')).toBeUndefined()
    expect(next.attributes('disabled')).toBeDefined()
  })

  it('emits update:page with the adjacent page number when clicked', async () => {
    const wrapper = mountPagination({ page: 2, count: 45, pageSize: 20 })

    const [previous, next] = wrapper.findAll('button')
    await previous.trigger('click')
    await next.trigger('click')

    expect(wrapper.emitted('update:page')).toEqual([[1], [3]])
  })
})
