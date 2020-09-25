'use strict';

var _slicedToArray = function () { function sliceIterator(arr, i) { var _arr = []; var _n = true; var _d = false; var _e = undefined; try { for (var _i = arr[Symbol.iterator](), _s; !(_n = (_s = _i.next()).done); _n = true) { _arr.push(_s.value); if (i && _arr.length === i) break; } } catch (err) { _d = true; _e = err; } finally { try { if (!_n && _i["return"]) _i["return"](); } finally { if (_d) throw _e; } } return _arr; } return function (arr, i) { if (Array.isArray(arr)) { return arr; } else if (Symbol.iterator in Object(arr)) { return sliceIterator(arr, i); } else { throw new TypeError("Invalid attempt to destructure non-iterable instance"); } }; }();

function _objectWithoutProperties(obj, keys) { var target = {}; for (var i in obj) { if (keys.indexOf(i) >= 0) continue; if (!Object.prototype.hasOwnProperty.call(obj, i)) continue; target[i] = obj[i]; } return target; }

function _toConsumableArray(arr) { if (Array.isArray(arr)) { for (var i = 0, arr2 = Array(arr.length); i < arr.length; i++) { arr2[i] = arr[i]; } return arr2; } else { return Array.from(arr); } }

function _defineProperty(obj, key, value) { if (key in obj) { Object.defineProperty(obj, key, { value: value, enumerable: true, configurable: true, writable: true }); } else { obj[key] = value; } return obj; }

var e = React.createElement;
var _React = React,
    useState = _React.useState,
    useRef = _React.useRef,
    useEffect = _React.useEffect;

var majors = JSON.parse(document.currentScript.getAttribute('data-majors'));
var dataRequired = JSON.parse(document.currentScript.getAttribute('data-required'));
var dataScoring = JSON.parse(document.currentScript.getAttribute('data-scoring'));
var dataSelectedMajors = JSON.parse(document.currentScript.getAttribute('data-selected-majors'));
var Form = function Form() {
  return React.createElement(
    'div',
    null,
    React.createElement(SelectMajors, null),
    React.createElement(RequiredCriteria, { initialTopics: dataRequired || [] }),
    React.createElement(ScoringCriteria, { initialTopics: dataScoring || [] })
  );
};
var SelectMajors = function SelectMajors() {
  var _useState = useState(dataSelectedMajors || []),
      _useState2 = _slicedToArray(_useState, 2),
      selectedMajors = _useState2[0],
      setSelectedMajors = _useState2[1];

  var inputRef = useRef();
  var jRef = useRef();
  var choices = majors.map(function (m) {
    return { label: m.title, value: m.id, raw: m };
  });
  // console.log(selectedMajors, dataSelectedMajors)
  // fix for jQuery
  jRef.current = { selectedMajors: selectedMajors };
  var toggleMajor = function toggleMajor(major) {
    var newSelectedMajors = jRef.current.selectedMajors.slice();
    var index = newSelectedMajors.findIndex(function (m) {
      return m.id == major.id;
    });
    if (index > -1) {
      newSelectedMajors.splice(index, 1);
    } else {
      newSelectedMajors.push(major);
    }
    setSelectedMajors(newSelectedMajors);
  };
  useEffect(function () {
    $(inputRef.current).autocomplete({
      source: choices,
      minLength: 0,
      select: function select(e, ui) {
        toggleMajor(ui.item.raw);
        $(inputRef.current).blur();
        return false;
      }
    }).focus(function () {
      $(inputRef.current).autocomplete('search');
    });
  }, []);

  return React.createElement(
    'div',
    { className: 'form-group' },
    React.createElement(
      'label',
      { htmlFor: 'majors' },
      '\u0E40\u0E25\u0E37\u0E2D\u0E01\u0E2A\u0E32\u0E02\u0E32'
    ),
    React.createElement('input', { ref: inputRef, className: 'form-control d-inline-block mb-2', id: 'search-major', name: 'search', type: 'text', placeholder: '\u0E04\u0E49\u0E19\u0E2B\u0E32\u0E0A\u0E37\u0E48\u0E2D\u0E2A\u0E32\u0E02\u0E32' }),
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
            '\u0E08\u0E33\u0E19\u0E27\u0E19\u0E23\u0E31\u0E1A (\u0E04\u0E19)'
          ),
          React.createElement('th', { scope: 'col' })
        )
      ),
      React.createElement(
        'tbody',
        null,
        selectedMajors.map(function (major, idx) {
          var _React$createElement;

          var label = major.title;
          return React.createElement(
            'tr',
            { key: 'major-' + major.id },
            React.createElement(
              'td',
              { scope: 'row' },
              label,
              React.createElement('input', (_React$createElement = { type: 'text', value: major.id }, _defineProperty(_React$createElement, 'type', 'hidden'), _defineProperty(_React$createElement, 'name', 'majors_' + (idx + 1) + '_id'), _defineProperty(_React$createElement, 'required', true), _React$createElement))
            ),
            React.createElement(
              'td',
              null,
              React.createElement('input', { type: 'number', className: 'form-control', name: 'majors_' + (idx + 1) + '_slot', defaultValue: major.slot, required: true })
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
    )
  );
};
var RequiredCriteria = function RequiredCriteria(_ref) {
  var _ref$initialTopics = _ref.initialTopics,
      initialTopics = _ref$initialTopics === undefined ? [] : _ref$initialTopics;

  var _useState3 = useState(initialTopics),
      _useState4 = _slicedToArray(_useState3, 2),
      topics = _useState4[0],
      setTopics = _useState4[1];

  var addNewTopic = function addNewTopic(e) {
    e.preventDefault();
    var newTopic = topics.slice();
    newTopic.push({ id: Date.now(), title: '', unit: '', children: [] });
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
  var _setSecondaryTopics = function _setSecondaryTopics(topicId, newSecondaryTopics) {
    var newTopics = topics.slice();
    var index = newTopics.findIndex(function (t) {
      return t.id === topicId;
    });
    newTopics[index] = Object.assign({}, newTopics[index], { children: newSecondaryTopics });
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
          return React.createElement(PrimaryTopic, {
            key: topic.id,
            topic: topic,
            removeTopic: removeTopic,
            number: idx + 1,
            secondaryTopics: topic.children,
            setSecondaryTopics: function setSecondaryTopics(newSecondaryTopics) {
              return _setSecondaryTopics(topic.id, newSecondaryTopics);
            }
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

var ScoringCriteria = function ScoringCriteria(_ref2) {
  var _ref2$initialTopics = _ref2.initialTopics,
      initialTopics = _ref2$initialTopics === undefined ? [] : _ref2$initialTopics;

  var _useState5 = useState(initialTopics),
      _useState6 = _slicedToArray(_useState5, 2),
      topics = _useState6[0],
      setTopics = _useState6[1];

  var addNewTopic = function addNewTopic(e) {
    e.preventDefault();
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
  var _setSecondaryTopics2 = function _setSecondaryTopics2(topicId, newSecondaryTopics) {
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
              return _setSecondaryTopics2(topic.id, newSecondaryTopics);
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
var PrimaryTopic = function PrimaryTopic(_ref3) {
  var topic = _ref3.topic,
      removeTopic = _ref3.removeTopic,
      number = _ref3.number,
      updateTopic = _ref3.updateTopic,
      secondaryTopics = _ref3.secondaryTopics,
      setSecondaryTopics = _ref3.setSecondaryTopics;

  var addNewTopic = function addNewTopic(e) {
    e.preventDefault();
    var newSecondaryTopics = secondaryTopics.slice();
    newSecondaryTopics.push({ id: Date.now(), title: '' });
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
      React.createElement(EditableCell, {
        name: 'required_' + number + '_title',
        initialValue: topic.title,
        focusOnMount: true,
        suffix: React.createElement(
          'div',
          { className: 'd-flex ml-2' },
          secondaryTopics.length > 0 && React.createElement(SelectRelation, { name: 'required_' + number + '_relation', relations: relationRequired, className: 'ml-2', initialValue: topic.relation || 'AND' }),
          React.createElement(
            'button',
            { className: 'btn btn-primary btn-sm ml-2', onClick: addNewTopic },
            '+'
          )
        ),
        inputProps: { required: true },
        tags: [].concat(_toConsumableArray(generalRequiredTags), _toConsumableArray(testTags))
      }),
      React.createElement(EditableCell, {
        name: 'required_' + number + '_value',
        initialValue: topic.value
      }),
      React.createElement(EditableCell, {
        name: 'required_' + number + '_unit',
        initialValue: topic.unit || '',
        tags: unitTags
      }),
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
      var snumber = number + '.' + (idx + 1);
      return React.createElement(
        'tr',
        { key: topic.id },
        React.createElement('td', null),
        React.createElement(EditableCell, {
          name: 'required_' + snumber + '_title',
          initialValue: topic.title,
          focusOnMount: true,
          prefix: React.createElement(
            'span',
            null,
            snumber,
            '\xA0\xA0'
          ),
          inputProps: { required: true },
          tags: [].concat(_toConsumableArray(generalRequiredTags), _toConsumableArray(testTags))
        }),
        React.createElement(EditableCell, {
          name: 'required_' + snumber + '_value',
          initialValue: topic.value
        }),
        React.createElement(EditableCell, {
          name: 'required_' + snumber + '_unit',
          initialValue: topic.unit,
          tags: unitTags
        }),
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
var PrimaryScoringTopic = function PrimaryScoringTopic(_ref4) {
  var topic = _ref4.topic,
      removeTopic = _ref4.removeTopic,
      number = _ref4.number,
      updateTopic = _ref4.updateTopic,
      maxScore = _ref4.maxScore,
      secondaryTopics = _ref4.secondaryTopics,
      setSecondaryTopics = _ref4.setSecondaryTopics;

  var addNewTopic = function addNewTopic(e) {
    e.preventDefault();
    var newSecondaryTopics = secondaryTopics.slice();
    newSecondaryTopics.push({ id: Date.now(), title: '', value: 1 });
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
  var updateSecondaryTopic = function updateSecondaryTopic(topicId, value) {
    var newSecondaryTopics = secondaryTopics.slice();
    var index = newSecondaryTopics.findIndex(function (t) {
      return t.id === topicId;
    });
    newSecondaryTopics[index] = Object.assign({}, newSecondaryTopics[index], value);
    setSecondaryTopics(newSecondaryTopics);
  };
  var primaryMaxScore = secondaryTopics.reduce(function (a, b) {
    return a + b.value;
  }, 0);
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
      React.createElement(EditableCell, {
        name: 'scoring_' + number + '_title',
        initialValue: topic.title,
        focusOnMount: true,
        suffix: React.createElement(
          'div',
          { className: 'd-flex' },
          secondaryTopics.length > 0 && React.createElement(SelectRelation, { name: 'scoring_' + number + '_relation', relations: relationScoring, className: 'ml-2', initialValue: topic.relation || 'SUM' }),
          React.createElement(
            'button',
            { className: 'btn btn-primary btn-sm ml-2', onClick: addNewTopic },
            '+'
          )
        ),
        inputProps: { required: true },
        tags: [].concat(_toConsumableArray(generalScoringTags), _toConsumableArray(testTags))
      }),
      React.createElement(EditableCell, {
        name: 'scoring_' + number + '_value',
        initialValue: topic.value,
        onSave: function onSave(v) {
          updateTopic(topic.id, { value: parseInt(v) });
        },
        inputType: 'number',
        inputProps: { required: true }
      }),
      React.createElement(
        'td',
        null,
        React.createElement(
          'strong',
          null,
          (topic.value / maxScore * 100).toLocaleString(),
          '%'
        )
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
      var snumber = number + '.' + (idx + 1);
      return React.createElement(
        'tr',
        { key: topic.id },
        React.createElement('td', null),
        React.createElement(EditableCell, {
          name: 'scoring_' + snumber + '_title',
          initialValue: topic.title,
          focusOnMount: true,
          prefix: React.createElement(
            'span',
            null,
            number,
            '.',
            idx + 1,
            '\xA0\xA0'
          ),
          inputProps: { required: true },
          tags: [].concat(_toConsumableArray(generalScoringTags), _toConsumableArray(testTags))
        }),
        React.createElement(EditableCell, {
          name: 'scoring_' + snumber + '_value',
          initialValue: topic.value,
          onSave: function onSave(v) {
            updateSecondaryTopic(topic.id, { value: parseInt(v) });
          },
          inputType: 'number',
          inputProps: { required: true }
        }),
        React.createElement(
          'td',
          null,
          (topic.value / primaryMaxScore * 100).toLocaleString(),
          '%'
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
var EditableCell = function EditableCell(_ref5) {
  var initialValue = _ref5.initialValue,
      _ref5$editable = _ref5.editable,
      editable = _ref5$editable === undefined ? true : _ref5$editable,
      _ref5$focusOnMount = _ref5.focusOnMount,
      focusOnMount = _ref5$focusOnMount === undefined ? false : _ref5$focusOnMount,
      children = _ref5.children,
      onSave = _ref5.onSave,
      prefix = _ref5.prefix,
      suffix = _ref5.suffix,
      inputType = _ref5.inputType,
      name = _ref5.name,
      inputProps = _ref5.inputProps,
      _ref5$tags = _ref5.tags,
      tags = _ref5$tags === undefined ? [] : _ref5$tags,
      restProps = _objectWithoutProperties(_ref5, ['initialValue', 'editable', 'focusOnMount', 'children', 'onSave', 'prefix', 'suffix', 'inputType', 'name', 'inputProps', 'tags']);

  var inputRef = useRef();
  useEffect(function () {
    if (editable) {
      $(inputRef.current).autocomplete({
        source: tags,
        minLength: 0
      }).focus(function () {
        if (inputRef.current.value == "") {
          $(inputRef.current).autocomplete("search");
        }
      });
    }
  }, [editable]);

  useEffect(function () {
    if (focusOnMount && !initialValue) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [focusOnMount]);
  var save = function save(e) {
    try {
      onSave && onSave(inputRef.current.value);
    } catch (errInfo) {
      console.log('Save failed:', errInfo);
    }
  };

  var calHeight = function calHeight() {
    inputRef.current.style.height = "";
    inputRef.current.style.height = inputRef.current.scrollHeight + 'px';
  };
  var childNode = initialValue;
  if (editable) {
    childNode = React.createElement(
      'div',
      { className: 'd-flex align-items-baseline' },
      prefix,
      inputType === 'number' ? React.createElement('input', Object.assign({ type: 'number', name: name, className: 'form-control d-inline-block', ref: inputRef, onChange: save, onBlur: save, defaultValue: initialValue }, inputProps)) : React.createElement('textarea', Object.assign({ className: 'form-control d-inline-block', rows: 1, name: name, ref: inputRef, onChange: calHeight, onBlur: save, defaultValue: initialValue }, inputProps)),
      suffix
    );
  }
  return React.createElement(
    'td',
    Object.assign({ style: { cursor: 'pointer' } }, restProps),
    ' ',
    childNode
  );
};
var SelectRelation = function SelectRelation(_ref6) {
  var name = _ref6.name,
      relations = _ref6.relations,
      className = _ref6.className,
      initialValue = _ref6.initialValue;

  console.log('initialValue', initialValue);
  return React.createElement(
    'select',
    { name: name, id: name, className: className, defaultValue: initialValue || null },
    React.createElement(
      'option',
      { disabled: true },
      '\u0E40\u0E25\u0E37\u0E2D\u0E01\u0E04\u0E27\u0E32\u0E21\u0E2A\u0E31\u0E21\u0E1E\u0E31\u0E19\u0E18\u0E4C'
    ),
    relations.map(function (r) {
      return React.createElement(
        'option',
        { value: r.value, key: r.value },
        r.label
      );
    })
  );
};

var domContainer = document.querySelector('#add-criterion-form');
ReactDOM.render(e(Form), domContainer);