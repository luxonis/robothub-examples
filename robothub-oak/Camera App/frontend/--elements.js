// RobotHubApi
let _streamStartedCbs = new Map();

robothubApi.onStreamStart = (cb) => {
  console.error("Calling on stream with ", cb)
    if (typeof cb === 'string') {
        for (const [_id, _cb] of _streamStartedCbs) {
          console.error("Calling")
        void _cb(cb);
        }
        return '';
    } else {
        const id = Math.random().toString(36).substring(2);
        _streamStartedCbs.set(id, cb);
        return id;
    }
}

document.getElementById('top-video').constructor.prototype.updateWidth = () => {
  console.error("Stream started or smth")
  // const wrapper = document.getElementById('top-video').shadowRoot.children[0]
  // const video = wrapper.children[0]
  // document.getElementById('top-video').updateWidth({ wrapper, canvas, video });
  // window.robothubApi.onStreamStart(document.getElementById('top-video').id);
    
}

robothubApi.offStreamStart = (id) => {
    _streamStartedCbs.delete(id);
}

robothubApi.whenSelected = (id, callback) => {
    const ids = Array.isArray(id) ? id : [id];
    document.addEventListener('selected', event => {
        if (!(event.target instanceof Element)) {
        return;
        }
        const target = event.target;
        if (ids.some(it => it === target.id) && target.getAttribute('disabled') !== 'true') {
        callback({ ...event, target: event.target, selected: event.detail });
        }
    });
}

robothubApi.whenSlid = (id, callback) => {
    const ids = Array.isArray(id) ? id : [id];
    document.addEventListener('slid', event => {
        if (!(event.target instanceof Element)) {
        return;
        }
        const target = event.target;
        if (ids.some(it => it === target.id) && target.getAttribute('disabled') !== 'true') {
        callback({ ...event, target: event.target, value: event.detail });
        }
    });
}

robothubApi.whenToggled = (id, callback) => {
    const ids = Array.isArray(id) ? id : [id];
    document.addEventListener('toggled', event => {
        if (!(event.target instanceof Element)) {
        return;
        }
        const target = event.target;
        if (ids.some(it => it === target.id) && target.getAttribute('disabled') !== 'true') {
        callback({ ...event, target: event.target, value: event.detail });
        }
    });
}

// Toggle
const toggleTemplate = document.createElement('template');
toggleTemplate.innerHTML = `
  <style>
    .rh-toggle {
      user-select: none;
    }
  </style>
  <div class="rh-toggle">
    <div data-is="switch" data-switch="off" data-disabled="true"></div>
  </div>
  <link rel="stylesheet" href="./--index.css" />
`;

class RobotHubToggle extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this.shadowRoot.appendChild(toggleTemplate.content.cloneNode(true));
  }

  connectedCallback() {
    this.setupListeners();
    this.updateDisplay();
  }

  setupListeners() {
    this.addEventListener('click', () => {
      this.toggleState();
    });
  }

  toggleState() {
    if (this.getAttribute('data-switch') == 'on') {
      this.setAttribute('data-switch', 'off');
    } else {
      this.setAttribute('data-switch', 'on');
    }
    this.dispatchEvent(new CustomEvent('toggled', {
      bubbles: true,
      detail: this.getAttribute('data-switch') == 'on'
    }));
    this.updateDisplay();
  }

  updateDisplay() {
    const switchElement = this.shadowRoot.querySelector('div[data-is=switch]');
    if (this.getAttribute('data-switch') == 'on') {
      switchElement.setAttribute('data-switch', 'on')
    } else {
      switchElement.setAttribute('data-switch', 'off')
    }
  }

  static get observedAttributes() {
    return ['on'];
  }

  attributeChangedCallback(name, oldValue, newValue) {
    if (oldValue !== newValue) {
      this.setAttribute('data-switch', newValue == 'true' ? 'on' : 'off');
      this.updateDisplay();
    }
  }
}

window.customElements.define('rh-toggle', RobotHubToggle);


// Option
const optionTemplate = document.createElement('template');
optionTemplate.innerHTML = `
  <style>
    .rh-option {
      user-select: none;
      display: flex;
      width: 100%;
      height: max-content;
      min-height: var(--_selectItemMinHeight);
      flex-direction: row;
      gap: var(--_selectItemGap);
      align-items: center;
      box-sizing: border-box;
      cursor: pointer;
      padding: var(--_selectItemVerticalPadding) var(--_selectItemHorizontalPadding);
    }

    .rh-option:hover {
      background-color: rgba(0, 0, 0, 0.04);
    }
  </style>
  <div class="rh-option" data-select="item">
    <slot></slot>
  </div>
  <link rel="stylesheet" href="./--index.css" />
`;

class RobotHubOption extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this.shadowRoot.appendChild(optionTemplate.content.cloneNode(true));
  }

  connectedCallback() {
    this.setupListeners();
  }

  setupListeners() {
    this.addEventListener('click', (event) => {
      event.stopPropagation();
      const selectElement = this.closest('rh-select');
      if (selectElement) {
        selectElement.select(this);
      }
    });
  }
}

window.customElements.define('rh-option', RobotHubOption);

// Select
const selectTemplate = document.createElement('template');
selectTemplate.innerHTML = `
  <style>
    .rh-select {
      user-select: none;
    }
  </style>
  <div class="rh-select">
    <div data-is="select">
      <div data-select="field">
        <div data-select="item"></div>
        <svg data-icon="true" viewBox="0 0 24 24">
          <path fill="currentColor" d="M7.41,8.58L12,13.17L16.59,8.58L18,10L12,16L6,10L7.41,8.58Z"></path>
        </svg>
      </div>

      <dialog data-select="dialog">
        <slot> </slot>
      </dialog>
    </div>
  </div>
  <link rel="stylesheet" href="./--index.css" />
`;

class RobotHubSelect extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this.shadowRoot.appendChild(selectTemplate.content.cloneNode(true));
    this._selected = this.shadowRoot.querySelector('div[data-select="item"]');
  }

  static get observedAttributes() {
    return ['id', 'open', 'selected'];
  }

  connectedCallback() {
    this.setupListeners();
    this.render();
  }

  disconnectedCallback() {
    this.removeListeners();
  }

  attributeChangedCallback(name, oldValue, newValue) {
    if (oldValue !== newValue) {
      this[name] = newValue;
      this.render();
    }
  }

  setupListeners() {
    const toggle = (event) => {
      if (event.target === this) {
        this.open = 'true';
      } else {
        this.open = 'false';
      }
      this.render();
    };

    document.addEventListener('click', toggle);
    this.removeListeners = () => {
      document.removeEventListener('click', toggle);
    };
  }

  render() {
    const dialog = this.shadowRoot.querySelector('dialog[data-select="dialog"]');
    if (!dialog) {
      throw new Error('Dialog element not found in shadow DOM');
    }
    if (this.open === 'true') {
      dialog.setAttribute('open', '');
    } else {
      dialog.removeAttribute('open');
    }
    const selectItem = this.shadowRoot.querySelector('div[data-select="item"]');
    if (selectItem) {
      selectItem.innerHTML = this._selected?.innerText || '';
      selectItem.mxid = this._selected?.mxid || '';
    }
  }

  select(option, quiet = false) {
    this.open = 'false';
    if (this._selected != option) {
      this._selected = option;
      if (!quiet) {
        this.dispatchEvent(new CustomEvent('selected', { bubbles: true, detail: option }));
      }
      this.render();
    }
    
  }

  get id() {
    return this.getAttribute('id') || 'select';
  }

  set id(value) {
    this.setAttribute('id', value);
  }

  get open() {
    return this.getAttribute('open') || 'false';
  }

  set open(value) {
    this.setAttribute('open', value);
  }

  get selected() {
    return this._selected;
  }

  set selected(value) {
    this._selected = value;
    this.setAttribute('selected', value.id);
  }
}

window.customElements.define('rh-select', RobotHubSelect);

// Slider
const sliderTemplate = document.createElement('template');
sliderTemplate.innerHTML = `
  <style>
    .rh-slider {
      user-select: none;
      padding: 1em 0.5em;
    }
  </style>
  <div class="rh-slider">
    <div data-is="slider" style="--_leftPadOffset:0%;">
      <div data-slider="track"></div>
      <span data-slider="min-value">0</span>
      <span data-slider="max-value">0</span>
      <div data-slider="left-pad"></div>
      <span data-slider="left-pad-value">0</span>
    </div>
  </div>
  <link rel="stylesheet" href="./--index.css" />
`;

class RobotHubSlider extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this.shadowRoot.appendChild(sliderTemplate.content.cloneNode(true));
    this.percentage = 0;
  }

  connectedCallback() {
    this.setAttribute('value', this.getAttribute('min'));
    this.setupListeners();
  }

  setupListeners() {
    this.addEventListener('mousedown', () => {
      const updateSlider = event => {
        const rect = this.getBoundingClientRect();
        let percentage = ((event.clientX - rect.x) / rect.width) * 100;

        percentage = this.stepped(
          percentage,
          parseFloat(this.getAttribute('min')),
          parseFloat(this.getAttribute('max')),
          parseFloat(this.getAttribute('step'))
        );
        if (this.percentage !== percentage) {
          this.update((percentage * parseFloat(this.getAttribute('max'))) / 100, percentage);
        }
      };
      document.addEventListener('mouseup', () => {
        document.removeEventListener('mouseup', updateSlider);
        document.removeEventListener('mousemove', updateSlider);
      });

      document.addEventListener('mousemove', updateSlider);
    });
  }

  stepped(value, min, max, step) {
    const numSteps = Math.round((value - min) / step);
    const result = min + step * numSteps;
    return Math.max(min, Math.min(max, result));
  }

  update(value, percentage) {
    const steppedValue = this.stepped(value, parseFloat(this.getAttribute('min')), parseFloat(this.getAttribute('max')), parseFloat(this.getAttribute('step')));
    this.setAttribute('value', steppedValue.toString());
    this.percentage = this.stepped(
      percentage,
      0,
      100,
      (parseFloat(this.getAttribute('step')) / (parseFloat(this.getAttribute('max')) - parseFloat(this.getAttribute('min')))) * 100,
    );
    this.dispatchEvent(new CustomEvent('slid', {
      bubbles: true,
      detail: steppedValue
    }));
    this.updateDisplay();
  }

  updateDisplay() {
    this.shadowRoot.querySelector('[data-slider="min-value"]').textContent = this.getAttribute('min');
    this.shadowRoot.querySelector('[data-slider="max-value"]').textContent = this.getAttribute('max');
    this.shadowRoot.querySelector('[data-is="slider"]').style.setProperty('--_leftPadOffset', `${this.percentage}%`);
    this.shadowRoot.querySelector('[data-slider="left-pad-value"]').textContent = this.getAttribute('value');
  }

  static get observedAttributes() {
    return ['min', 'max', 'step', 'value'];
  }

  attributeChangedCallback(name, oldValue, newValue) {
    if (oldValue !== newValue) {
      if (name == 'value') {
        this.percentage = (newValue - this.getAttribute('min')) / (this.getAttribute('max') - this.getAttribute('min')) * 100
      }
      this.updateDisplay();
    }
  }
}

window.customElements.define('rh-slider', RobotHubSlider);

// Text
// Define our custom element
class RobotHubText extends HTMLElement {
  constructor() {
      super();
      // Attach shadow DOM to the custom element
      this.attachShadow({ mode: 'open' });
  }

  connectedCallback() {
      this.render();
  }

  attributeChangedCallback(attribute, oldValue, newValue) {
      if (oldValue !== newValue) {
          this.render();
      }
  }

  get size() {
      return this.getAttribute('size') || 'md';
  }

  get color() {
      return this.getAttribute('color') || 'primary';
  }

  get weight() {
      return this.getAttribute('weight') || 'normal';
  }

  render() {
      this.shadowRoot.innerHTML = `
          <style>
              .rh-text {
              }
          </style>
          <span class="rh-text"
              data-text="text-${this.size}"
              data-text-color="${this.color}"
              data-text-weight="${this.weight}"
          >
              <slot></slot>
          </span>
          <link rel="stylesheet" href="./--index.css" />
      `;
  }

  // static get observedAttributes lists the attributes we care about
  static get observedAttributes() {
      return ['size', 'color', 'weight'];
  }
}

// Define the new element
window.customElements.define('rh-text', RobotHubText);
