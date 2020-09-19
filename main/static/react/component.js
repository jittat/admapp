'use strict';

var _slicedToArray = function () { function sliceIterator(arr, i) { var _arr = []; var _n = true; var _d = false; var _e = undefined; try { for (var _i = arr[Symbol.iterator](), _s; !(_n = (_s = _i.next()).done); _n = true) { _arr.push(_s.value); if (i && _arr.length === i) break; } } catch (err) { _d = true; _e = err; } finally { try { if (!_n && _i["return"]) _i["return"](); } finally { if (_d) throw _e; } } return _arr; } return function (arr, i) { if (Array.isArray(arr)) { return arr; } else if (Symbol.iterator in Object(arr)) { return sliceIterator(arr, i); } else { throw new TypeError("Invalid attempt to destructure non-iterable instance"); } }; }();

var e = React.createElement;
var _React = React,
    useState = _React.useState;


var majors = [{
  program_id: '10020112610501A',
  faculty_name_th: 'คณะบริหารธุรกิจ',
  program_name_th: 'บช.บ.',
  program_type_name_th: 'ภาษาไทย ปกติ'
}, {
  program_id: '10020111901802B',
  faculty_name_th: 'คณะมนุษยศาสตร์',
  program_name_th: 'ศศ.บ. สาขาวิชาภาษาจีนธุรกิจ',
  program_type_name_th: 'ภาษาไทย พิเศษ'
}, {
  program_id: '10020104212701A',
  faculty_name_th: 'คณะวิทยาศาสตร์',
  program_name_th: 'วท.บ. สาขาวิชาฟิสิกส์',
  program_type_name_th: 'ภาษาไทย ปกติ'
}, {
  program_id: '10020104220201B',
  faculty_name_th: 'คณะวิทยาศาสตร์',
  program_name_th: 'วท.บ. สาขาวิชาวิทยาการคอมพิวเตอร์',
  program_type_name_th: 'ภาษาไทย ปกติ'
}, {
  program_id: '10020104210702A',
  faculty_name_th: 'คณะวิทยาศาสตร์',
  program_name_th: 'วท.บ. สาขาวิชาวิทยาศาสตร์ชีวภาพรังสี',
  program_type_name_th: 'ภาษาไทย พิเศษ'
}, {
  program_id: '10020104213301A',
  faculty_name_th: 'คณะวิทยาศาสตร์',
  program_name_th: 'วท.บ. สาขาวิชาสถิติ',
  program_type_name_th: 'ภาษาไทย ปกติ'
}];
var Form = function Form() {
  var _useState = useState(''),
      _useState2 = _slicedToArray(_useState, 2),
      search = _useState2[0],
      setSearch = _useState2[1];

  var _useState3 = useState([]),
      _useState4 = _slicedToArray(_useState3, 2),
      selectedMajors = _useState4[0],
      setSelectedMajors = _useState4[1];

  var selectMajor = function selectMajor(major) {
    var newSelectedMajors = selectedMajors.slice();
    var index = newSelectedMajors.findIndex(function (m) {
      return m.program_id === major.program_id;
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
            var label = major.faculty_name_th + ' ' + major.program_name_th;
            if (label.toUpperCase().indexOf(search) > -1) return React.createElement(
              'a',
              {
                href: '#',
                key: major.program_id,
                className: 'list-group-item list-group-item-action',
                onClick: function onClick() {
                  selectMajor(major);
                }
              },
              label
            );
          })
        )
      ),
      selectedMajors.map(function (major) {
        var label = major.faculty_name_th + ' ' + major.program_name_th;
        return React.createElement(
          'div',
          null,
          label
        );
      })
    )
  );
};

var domContainer = document.querySelector('#add-criterion-form');
ReactDOM.render(e(Form), domContainer);