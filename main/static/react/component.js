'use strict';

var _slicedToArray = function () { function sliceIterator(arr, i) { var _arr = []; var _n = true; var _d = false; var _e = undefined; try { for (var _i = arr[Symbol.iterator](), _s; !(_n = (_s = _i.next()).done); _n = true) { _arr.push(_s.value); if (i && _arr.length === i) break; } } catch (err) { _d = true; _e = err; } finally { try { if (!_n && _i["return"]) _i["return"](); } finally { if (_d) throw _e; } } return _arr; } return function (arr, i) { if (Array.isArray(arr)) { return arr; } else if (Symbol.iterator in Object(arr)) { return sliceIterator(arr, i); } else { throw new TypeError("Invalid attempt to destructure non-iterable instance"); } }; }();

function _objectWithoutProperties(obj, keys) { var target = {}; for (var i in obj) { if (keys.indexOf(i) >= 0) continue; if (!Object.prototype.hasOwnProperty.call(obj, i)) continue; target[i] = obj[i]; } return target; }

var e = React.createElement;
var _React = React,
    useState = _React.useState,
    useRef = _React.useRef,
    useEffect = _React.useEffect;

var majors = JSON.parse(document.currentScript.getAttribute('data-majors'));
var Form = function Form() {
  var _useState = useState(''),
      _useState2 = _slicedToArray(_useState, 2),
      search = _useState2[0],
      setSearch = _useState2[1];

  var _useState3 = useState([{ id: 1, title: 'PAT 1', value: 22, unit: 'หน่วยกิต' }, { id: 2, title: 'PAT 2', value: 22, unit: 'หน่วยกิต', children: [{ id: 2.1, title: 'PAT 2.2', value: 22, unit: 'หน่วยกิต' }] }]),
      _useState4 = _slicedToArray(_useState3, 2),
      topics = _useState4[0],
      setTopics = _useState4[1];

  var _useState5 = useState([]),
      _useState6 = _slicedToArray(_useState5, 2),
      selectedMajors = _useState6[0],
      setSelectedMajors = _useState6[1];

  var toggleMajor = function toggleMajor(major) {
    var newSelectedMajors = selectedMajors.slice();
    var index = newSelectedMajors.findIndex(function (m) {
      return m.id === major.id;
    });
    if (index > -1) {
      newSelectedMajors.splice(index, 1);
    } else {
      newSelectedMajors.push(major);
    }
    setSelectedMajors(newSelectedMajors);
  };
  var addNewTopic = function addNewTopic(topic) {
    var lastTopic = topics.length ? topics[topics.length - 1] : null;
    var nextId = lastTopic ? lastTopic.id + 1 : 1;
    var newTopic = topics.slice();
    newTopic.push({ id: nextId, title: '', value: '', unit: '' });
    setTopics(newTopic);
  };
  return React.createElement(
    'div',
    null,
    React.createElement(
      'form',
      null,
      React.createElement(
        'div',
        { className: 'form-group' },
        React.createElement(
          'label',
          { htmlFor: 'majors' },
          '\u0E40\u0E25\u0E37\u0E2D\u0E01\u0E2A\u0E32\u0E02\u0E32'
        ),
        React.createElement('input', {
          type: 'text',
          id: 'majors',
          className: 'form-control',
          onKeyUp: function onKeyUp(e) {
            setSearch(e.target.value.toUpperCase());
          },
          placeholder: '\u0E04\u0E49\u0E19\u0E2B\u0E32\u0E0A\u0E37\u0E48\u0E2D\u0E04\u0E13\u0E30/\u0E2A\u0E32\u0E02\u0E32'
        }),
        React.createElement(
          'div',
          { className: 'list-group', style: { zIndex: 1, height: 300, overflow: 'auto' } },
          majors.map(function (major) {
            var label = major.title;
            if (label.toUpperCase().indexOf(search) > -1) return React.createElement(
              'a',
              {
                href: '#',
                key: major.id,
                className: 'list-group-item list-group-item-action',
                onClick: function onClick() {
                  toggleMajor(major);
                }
              },
              label
            );
          })
        )
      ),
      selectedMajors.length > 0 && React.createElement(
        'table',
        { className: 'table table-bordered' },
        React.createElement(
          'thead',
          null,
          React.createElement(
            'tr',
            null,
            React.createElement(
              'th',
              { scope: 'col' },
              '\u0E2A\u0E32\u0E02\u0E32'
            ),
            React.createElement(
              'th',
              { scope: 'col' },
              '\u0E08\u0E33\u0E19\u0E27\u0E19\u0E23\u0E31\u0E1A'
            ),
            React.createElement('th', { scope: 'col' })
          )
        ),
        React.createElement(
          'tbody',
          null,
          selectedMajors.map(function (major) {
            var label = major.title;
            return React.createElement(
              'tr',
              { key: 'major-' + major.id },
              React.createElement(
                'td',
                { scope: 'row' },
                label
              ),
              React.createElement(
                'td',
                null,
                React.createElement('input', { type: 'number', className: 'form-control' })
              ),
              React.createElement(
                'td',
                null,
                React.createElement(
                  'button',
                  { htmltype: 'button', className: 'btn btn-secondary', onClick: function onClick() {
                      return toggleMajor(major);
                    } },
                  '\u0E25\u0E1A'
                )
              )
            );
          })
        )
      ),
      React.createElement(
        'div',
        { className: 'form-group' },
        React.createElement(
          'label',
          { htmlFor: 'majors' },
          '\u0E04\u0E38\u0E13\u0E2A\u0E21\u0E1A\u0E31\u0E15\u0E34\u0E40\u0E09\u0E1E\u0E32\u0E30'
        ),
        React.createElement(
          'table',
          { className: 'table table-bordered' },
          React.createElement(
            'thead',
            null,
            React.createElement(
              'tr',
              null,
              React.createElement('th', null),
              React.createElement('th', null),
              React.createElement('th', null),
              React.createElement(
                'th',
                null,
                '\u0E2B\u0E19\u0E48\u0E27\u0E22'
              )
            )
          ),
          React.createElement(
            'tbody',
            null,
            topics.map(function (topic) {
              return React.createElement(PrimaryTopic, { topic: topic });
            })
          )
        ),
        React.createElement(
          'div',
          { className: 'btn btn-primary', onClick: addNewTopic },
          '+'
        )
      )
    )
  );
};
var PrimaryTopic = function PrimaryTopic(_ref) {
  var topic = _ref.topic;

  var _useState7 = useState([]),
      _useState8 = _slicedToArray(_useState7, 2),
      secondaryTopics = _useState8[0],
      setSecondaryTopics = _useState8[1];

  var addNewTopic = function addNewTopic() {
    var newSecondaryTopics = secondaryTopics.slice();
    newSecondaryTopics.push({ id: topic.id + '.' + (secondaryTopics.length + 1), title: '', value: '', unit: '' });
    console.log(newSecondaryTopics);
    setSecondaryTopics(newSecondaryTopics);
  };
  return React.createElement(
    React.Fragment,
    null,
    React.createElement(
      'tr',
      null,
      React.createElement(
        'td',
        null,
        topic.id,
        React.createElement(
          'div',
          { className: 'btn btn-primary', onClick: addNewTopic },
          '+'
        )
      ),
      React.createElement(EditableCell, { initialValue: topic.title, focusOnMount: true }),
      React.createElement(EditableCell, { initialValue: topic.value }),
      React.createElement(EditableCell, { initialValue: topic.unit })
    ),
    secondaryTopics.map(function (topic) {
      return React.createElement(
        'tr',
        null,
        React.createElement(
          'td',
          null,
          topic.id
        ),
        React.createElement(EditableCell, { initialValue: topic.title, focusOnMount: true }),
        React.createElement(EditableCell, { initialValue: topic.value }),
        React.createElement(EditableCell, { initialValue: topic.unit })
      );
    })
  );
};
var EditableCell = function EditableCell(_ref2) {
  var initialValue = _ref2.initialValue,
      _ref2$editable = _ref2.editable,
      editable = _ref2$editable === undefined ? true : _ref2$editable,
      _ref2$focusOnMount = _ref2.focusOnMount,
      focusOnMount = _ref2$focusOnMount === undefined ? false : _ref2$focusOnMount,
      children = _ref2.children,
      handleSave = _ref2.handleSave,
      restProps = _objectWithoutProperties(_ref2, ['initialValue', 'editable', 'focusOnMount', 'children', 'handleSave']);

  var _useState9 = useState(focusOnMount),
      _useState10 = _slicedToArray(_useState9, 2),
      editing = _useState10[0],
      setEditing = _useState10[1];

  var _useState11 = useState(initialValue),
      _useState12 = _slicedToArray(_useState11, 2),
      value = _useState12[0],
      setValue = _useState12[1];

  var inputRef = useRef();
  var toggleEdit = function toggleEdit() {
    setEditing(!editing);
  };

  useEffect(function () {
    if (editing) {
      inputRef.current.focus();
    }
  }, [editing]);
  var save = function save(e) {
    try {
      toggleEdit();
    } catch (errInfo) {
      console.log('Save failed:', errInfo);
    }
  };

  var childNode = value;
  if (editable) {
    childNode = editing ? React.createElement(
      'div',
      { className: 'form-group'
      },
      React.createElement('input', { ref: inputRef, onPressEnter: save, onBlur: save, value: value, onChange: function onChange(e) {
          return setValue(e.target.value);
        } })
    ) : React.createElement(
      'button',
      { className: 'btn btn-default', style: { paddingRight: 24 }, onClick: toggleEdit },
      value
    );
  }
  return React.createElement(
    'td',
    restProps,
    childNode
  );
};

var domContainer = document.querySelector('#add-criterion-form');
ReactDOM.render(e(Form), domContainer);