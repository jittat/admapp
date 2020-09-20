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

  var _useState3 = useState([]),
      _useState4 = _slicedToArray(_useState3, 2),
      selectedMajors = _useState4[0],
      setSelectedMajors = _useState4[1];

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
      React.createElement(RequiredCriteria, null),
      React.createElement(ScoringCriteria, null)
    )
  );
};
var RequiredCriteria = function RequiredCriteria() {
  var _useState5 = useState([{ id: 1, title: 'PAT 1', value: 22, unit: 'หน่วยกิต' }, { id: 2, title: 'PAT 2', value: 22, unit: 'หน่วยกิต', children: [{ id: 2.1, title: 'PAT 2.2', value: 22, unit: 'หน่วยกิต' }] }]),
      _useState6 = _slicedToArray(_useState5, 2),
      topics = _useState6[0],
      setTopics = _useState6[1];

  var addNewTopic = function addNewTopic(topic) {
    var newTopic = topics.slice();
    newTopic.push({ id: Date.now(), title: '', value: '', unit: '' });
    setTopics(newTopic);
  };
  var removeTopic = function removeTopic(topic) {
    var newTopics = topics.slice();
    var index = newTopics.findIndex(function (t) {
      return t.id === topic.id;
    });
    newTopics.splice(index, 1);
    setTopics(newTopics);
  };
  return React.createElement(
    'div',
    { className: 'form-group' },
    React.createElement(
      'label',
      { htmlFor: 'majors' },
      '\u0E04\u0E38\u0E13\u0E2A\u0E21\u0E1A\u0E31\u0E15\u0E34\u0E40\u0E09\u0E1E\u0E32\u0E30'
    ),
    React.createElement(
      'small',
      { className: 'form-text text-muted' },
      '\u0E04\u0E38\u0E13\u0E2A\u0E21\u0E1A\u0E31\u0E15\u0E34\u0E41\u0E25\u0E30\u0E04\u0E30\u0E41\u0E19\u0E19\u0E02\u0E31\u0E49\u0E19\u0E15\u0E48\u0E33 \u0E40\u0E0A\u0E48\u0E19 O-NET \u0E20\u0E32\u0E29\u0E32\u0E2D\u0E31\u0E07\u0E01\u0E24\u0E29 \u0E21\u0E32\u0E01\u0E01\u0E27\u0E48\u0E32 16 \u0E04\u0E30\u0E41\u0E19\u0E19'
    ),
    React.createElement(
      'table',
      { className: 'table table-bordered', style: { tableLayout: 'fixed' } },
      React.createElement(
        'thead',
        null,
        React.createElement(
          'tr',
          null,
          React.createElement('th', { style: { width: '5%' } }),
          React.createElement('th', null),
          React.createElement(
            'th',
            { style: { width: '15%' } },
            '\u0E02\u0E31\u0E49\u0E19\u0E15\u0E48\u0E33 (\u2265)'
          ),
          React.createElement(
            'th',
            { style: { width: '15%' } },
            '\u0E2B\u0E19\u0E48\u0E27\u0E22'
          ),
          React.createElement('th', { style: { width: '5%' } })
        )
      ),
      React.createElement(
        'tbody',
        null,
        topics.map(function (topic, idx) {
          return React.createElement(PrimaryTopic, { key: topic.id, topic: topic, removeTopic: removeTopic, number: idx + 1 });
        }),
        React.createElement(
          'tr',
          null,
          React.createElement(
            'td',
            null,
            React.createElement(
              'div',
              { className: 'btn btn-primary', onClick: addNewTopic },
              '+'
            )
          ),
          React.createElement('td', null),
          React.createElement('td', null),
          React.createElement('td', null),
          React.createElement('td', null)
        )
      )
    )
  );
};

var ScoringCriteria = function ScoringCriteria() {
  var _useState7 = useState([{ id: 1, title: 'ผลการเรียนเฉลี่ยสะสม (GPAX)', value: 1, children: [{ id: 1.1, title: 'ผลการเรียนเฉลี่ยสะสม (GPAX)', value: 1 }] }, { id: 2, title: 'การสอบปฏิบัติเครื่องดนตรีตะวันตก', value: 1, children: [{ id: 2.1, title: 'ความรู้พื้นฐานทางทฤษฎีและประวัติศาสตร์ดนตรีตะวันตก', value: 1 }] }]),
      _useState8 = _slicedToArray(_useState7, 2),
      topics = _useState8[0],
      setTopics = _useState8[1];

  var addNewTopic = function addNewTopic() {
    var newTopic = topics.slice();
    newTopic.push({ id: Date.now(), title: '', value: 1, children: [] });
    console.log(newTopic);
    setTopics(newTopic);
  };
  var removeTopic = function removeTopic(topic) {
    var newTopics = topics.slice();
    var index = newTopics.findIndex(function (t) {
      return t.id === topic.id;
    });
    newTopics.splice(index, 1);
    setTopics(newTopics);
  };
  var updateTopic = function updateTopic(topicId, value) {
    console.log('Updating topic', topicId, value);
    var newTopics = topics.slice();
    var index = newTopics.findIndex(function (t) {
      return t.id === topicId;
    });
    newTopics[index] = Object.assign({}, newTopics[index], value);
    setTopics(newTopics);
  };
  var _setSecondaryTopics = function _setSecondaryTopics(topicId, newSecondaryTopics) {
    var newTopics = topics.slice();
    var index = newTopics.findIndex(function (t) {
      return t.id === topicId;
    });
    newTopics[index] = Object.assign({}, newTopics[index], { children: newSecondaryTopics });
    setTopics(newTopics);
  };
  var maxScore = topics.reduce(function (a, b) {
    return a + b.value;
  }, 0);
  return React.createElement(
    'div',
    { className: 'form-group' },
    React.createElement(
      'label',
      { htmlFor: 'majors' },
      '\u0E40\u0E01\u0E13\u0E11\u0E4C\u0E01\u0E32\u0E23\u0E04\u0E31\u0E14\u0E40\u0E25\u0E37\u0E2D\u0E01'
    ),
    React.createElement(
      'small',
      { className: 'form-text text-muted' },
      '\u0E40\u0E01\u0E13\u0E11\u0E4C\u0E2A\u0E33\u0E2B\u0E23\u0E31\u0E1A\u0E04\u0E33\u0E19\u0E27\u0E19\u0E04\u0E30\u0E41\u0E19\u0E19 \u0E08\u0E31\u0E14\u0E25\u0E33\u0E14\u0E31\u0E1A \u0E40\u0E0A\u0E48\u0E19 GAT 50%, PAT-1 50%'
    ),
    React.createElement(
      'table',
      { className: 'table table-bordered', style: { tableLayout: 'fixed' } },
      React.createElement(
        'thead',
        null,
        React.createElement(
          'tr',
          null,
          React.createElement('th', { style: { width: '5%' } }),
          React.createElement('th', null),
          React.createElement(
            'th',
            { style: { width: '15%' } },
            '\u0E2A\u0E31\u0E14\u0E2A\u0E48\u0E27\u0E19\u0E04\u0E30\u0E41\u0E19\u0E19'
          ),
          React.createElement(
            'th',
            { style: { width: '15%' } },
            '\u0E23\u0E49\u0E2D\u0E22\u0E25\u0E30'
          ),
          React.createElement('th', { style: { width: '5%' } })
        )
      ),
      React.createElement(
        'tbody',
        null,
        topics.map(function (topic, idx) {
          return React.createElement(PrimaryScoringTopic, {
            topic: topic,
            updateTopic: updateTopic,
            removeTopic: removeTopic,
            number: idx + 1,
            maxScore: maxScore,
            secondaryTopics: topic.children,
            setSecondaryTopics: function setSecondaryTopics(newSecondaryTopics) {
              return _setSecondaryTopics(topic.id, newSecondaryTopics);
            },
            key: topic.id
          });
        }),
        React.createElement(
          'tr',
          null,
          React.createElement(
            'td',
            null,
            React.createElement(
              'div',
              { className: 'btn btn-primary', onClick: addNewTopic },
              '+'
            )
          ),
          React.createElement('td', null),
          React.createElement('td', null),
          React.createElement('td', null),
          React.createElement('td', null)
        )
      )
    )
  );
};
var PrimaryTopic = function PrimaryTopic(_ref) {
  var topic = _ref.topic,
      removeTopic = _ref.removeTopic,
      number = _ref.number;

  var _useState9 = useState([]),
      _useState10 = _slicedToArray(_useState9, 2),
      secondaryTopics = _useState10[0],
      setSecondaryTopics = _useState10[1];

  var addNewTopic = function addNewTopic() {
    var newSecondaryTopics = secondaryTopics.slice();
    newSecondaryTopics.push({ id: Date.now(), title: '', value: '', unit: '' });
    setSecondaryTopics(newSecondaryTopics);
  };

  var removeSecondaryTopic = function removeSecondaryTopic(topic) {
    var newSecondaryTopics = secondaryTopics.slice();
    var index = newSecondaryTopics.findIndex(function (t) {
      return t.id === topic.id;
    });
    newSecondaryTopics.splice(index, 1);
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
        number
      ),
      React.createElement(EditableCell, { initialValue: topic.title, focusOnMount: true, suffix: React.createElement(
          'div',
          null,
          React.createElement(
            'button',
            { className: 'btn btn-primary btn-sm', onClick: addNewTopic },
            '+'
          )
        ) }),
      React.createElement(EditableCell, { initialValue: topic.value }),
      React.createElement(EditableCell, { initialValue: topic.unit }),
      React.createElement(
        'td',
        null,
        React.createElement(
          'button',
          { className: 'btn btn-secondary btn-sm', onClick: function onClick() {
              return removeTopic(topic);
            } },
          '-'
        )
      )
    ),
    secondaryTopics.map(function (topic, idx) {
      return React.createElement(
        'tr',
        { key: topic.id },
        React.createElement('td', null),
        React.createElement(EditableCell, { initialValue: topic.title, focusOnMount: true, prefix: React.createElement(
            'span',
            null,
            '\xA0 \xA0 \xA0 \xA0',
            number,
            '.',
            idx + 1,
            '\xA0\xA0'
          ) }),
        React.createElement(EditableCell, { initialValue: topic.value }),
        React.createElement(EditableCell, { initialValue: topic.unit }),
        React.createElement(
          'td',
          null,
          React.createElement(
            'button',
            { className: 'btn btn-secondary btn-sm', onClick: function onClick() {
                return removeSecondaryTopic(topic);
              } },
            '-'
          )
        )
      );
    })
  );
};
var PrimaryScoringTopic = function PrimaryScoringTopic(_ref2) {
  var topic = _ref2.topic,
      removeTopic = _ref2.removeTopic,
      number = _ref2.number,
      updateTopic = _ref2.updateTopic,
      maxScore = _ref2.maxScore,
      secondaryTopics = _ref2.secondaryTopics,
      setSecondaryTopics = _ref2.setSecondaryTopics;

  var addNewTopic = function addNewTopic(e) {
    console.log('eiei');
    // e.stopPropagation()
    var newSecondaryTopics = secondaryTopics.slice();
    newSecondaryTopics.push({ id: Date.now(), title: '', value: 1 });
    console.log('addNewTopic', newSecondaryTopics);
    setSecondaryTopics(newSecondaryTopics);
  };
  var removeSecondaryTopic = function removeSecondaryTopic(topic) {
    var newSecondaryTopics = secondaryTopics.slice();
    var index = newSecondaryTopics.findIndex(function (t) {
      return t.id === topic.id;
    });
    newSecondaryTopics.splice(index, 1);
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
        number
      ),
      React.createElement(EditableCell, { initialValue: topic.title, focusOnMount: true, suffix: React.createElement(
          'div',
          null,
          React.createElement(
            'button',
            { className: 'btn btn-primary btn-sm', onClick: addNewTopic },
            '+'
          )
        ) }),
      React.createElement(EditableCell, { initialValue: topic.value, onSave: function onSave(v) {
          updateTopic(topic.id, { value: v });
        }, inputType: 'number' }),
      React.createElement(
        'td',
        null,
        (topic.value / maxScore * 100).toPrecision(2),
        '%'
      ),
      React.createElement(
        'td',
        null,
        React.createElement(
          'button',
          { className: 'btn btn-secondary btn-sm', onClick: function onClick() {
              return removeTopic(topic);
            } },
          '-'
        )
      )
    ),
    secondaryTopics.map(function (topic, idx) {
      return React.createElement(
        'tr',
        { key: topic.id },
        React.createElement('td', null),
        React.createElement(EditableCell, { initialValue: topic.title, focusOnMount: true, prefix: React.createElement(
            'span',
            null,
            '\xA0 \xA0 \xA0 \xA0',
            number,
            '.',
            idx + 1,
            '\xA0\xA0'
          ) }),
        React.createElement(EditableCell, { initialValue: topic.value }),
        React.createElement(
          'td',
          null,
          '3%'
        ),
        React.createElement(
          'td',
          null,
          React.createElement(
            'button',
            { className: 'btn btn-secondary btn-sm', onClick: function onClick() {
                return removeSecondaryTopic(topic);
              } },
            '-'
          )
        )
      );
    })
  );
};
var EditableCell = function EditableCell(_ref3) {
  var initialValue = _ref3.initialValue,
      _ref3$editable = _ref3.editable,
      editable = _ref3$editable === undefined ? true : _ref3$editable,
      _ref3$focusOnMount = _ref3.focusOnMount,
      focusOnMount = _ref3$focusOnMount === undefined ? false : _ref3$focusOnMount,
      children = _ref3.children,
      onSave = _ref3.onSave,
      prefix = _ref3.prefix,
      suffix = _ref3.suffix,
      inputType = _ref3.inputType,
      restProps = _objectWithoutProperties(_ref3, ['initialValue', 'editable', 'focusOnMount', 'children', 'onSave', 'prefix', 'suffix', 'inputType']);

  var _useState11 = useState(focusOnMount),
      _useState12 = _slicedToArray(_useState11, 2),
      editing = _useState12[0],
      setEditing = _useState12[1];

  var _useState13 = useState(initialValue),
      _useState14 = _slicedToArray(_useState13, 2),
      value = _useState14[0],
      setValue = _useState14[1];

  var inputRef = useRef();
  var toggleEdit = function toggleEdit() {
    setEditing(!editing);
  };
  useEffect(function () {
    var availableTags = ["ActionScript", "AppleScript", "Asp", "BASIC", "C", "C++", "Clojure", "COBOL", "ColdFusion", "Erlang", "Fortran", "Groovy", "Haskell", "Java", "JavaScript", "Lisp", "Perl", "PHP", "Python", "Ruby", "Scala", "Scheme"];
    if (editing) {
      $(inputRef.current).autocomplete({
        source: availableTags
      });
    }
  }, [editing]);

  useEffect(function () {
    if (editing) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [editing]);
  var save = function save(e) {
    try {
      toggleEdit();
      setValue(inputRef.current.value);
      onSave && onSave(inputRef.current.value);
    } catch (errInfo) {
      console.log('Save failed:', errInfo);
    }
  };

  var childNode = value;
  if (editable) {
    childNode = editing ? React.createElement(
      'div',
      { className: 'form-group d-flex'
      },
      prefix,
      inputType === 'number' ? React.createElement('input', { type: 'text', className: 'form-control d-inline-block', ref: inputRef, onPressEnter: save, onBlur: save, defaultValue: value }) : React.createElement('textarea', { className: 'form-control  d-inline-block', ref: inputRef, onPressEnter: save, onBlur: save, defaultValue: value })
    ) : React.createElement(
      'div',
      { className: 'form-group d-flex' },
      React.createElement(
        'button',
        { className: 'btn', style: { textAlign: 'left', width: '100%', whiteSpace: 'pre-wrap' }, onClick: toggleEdit },
        prefix,
        value
      ),
      suffix
    );
  }
  return React.createElement(
    'td',
    Object.assign({ onClick: toggleEdit, style: { cursor: 'pointer' } }, restProps),
    ' ',
    childNode
  );
};

var domContainer = document.querySelector('#add-criterion-form');
ReactDOM.render(e(Form), domContainer);