'use strict';

function _extends() { _extends = Object.assign ? Object.assign.bind() : function (target) { for (var i = 1; i < arguments.length; i++) { var source = arguments[i]; for (var key in source) { if (Object.prototype.hasOwnProperty.call(source, key)) { target[key] = source[key]; } } } return target; }; return _extends.apply(this, arguments); }
const e = React.createElement;
const {
  useState,
  useRef,
  useEffect
} = React;
let majors = JSON.parse(document.currentScript.getAttribute('data-majors'));
let dataRequired = JSON.parse(document.currentScript.getAttribute('data-required'));
let dataScoring = JSON.parse(document.currentScript.getAttribute('data-scoring'));
let dataSelectedMajors = JSON.parse(document.currentScript.getAttribute('data-selected-majors'));
let mode = document.currentScript.getAttribute('data-mode');
let _isCustomScoreCriteriaAllowed = document.currentScript.getAttribute('data-is_custom_score_criteria_allowed') === 'True';
const MODE = {
  CREATE: 'create',
  EDIT: 'edit'
};
const RELATION_MAX = "MAX";
const Form = () => {
  // console.log(dataRequired)
  // console.log(dataScoring)
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(SelectMajors, null), !hideRequiredSection && /*#__PURE__*/React.createElement(RequiredCriteria, {
    initialTopics: dataRequired || []
  }), /*#__PURE__*/React.createElement(ScoringCriteria, {
    initialTopics: dataScoring || []
  }));
};
const SelectMajors = () => {
  const [selectedMajors, setSelectedMajors] = useState(dataSelectedMajors || []);
  const inputRef = useRef();
  const jRef = useRef();
  const choices = majors.map(m => ({
    label: m.title,
    value: m.id,
    raw: m
  }));
  // console.log(selectedMajors, dataSelectedMajors)
  // fix for jQuery
  jRef.current = {
    selectedMajors: selectedMajors
  };
  const toggleMajor = major => {
    const newSelectedMajors = jRef.current.selectedMajors.slice();
    const index = newSelectedMajors.findIndex(m => m.id == major.id);
    if (index > -1) {
      newSelectedMajors.splice(index, 1);
    } else {
      newSelectedMajors.push(major);
    }
    setSelectedMajors(newSelectedMajors);
  };
  useEffect(() => {
    $(inputRef.current).autocomplete({
      source: choices,
      minLength: 0,
      select: (e, ui) => {
        toggleMajor(ui.item.raw);
        $(inputRef.current).blur();
        return false;
      }
    }).focus(function () {
      $(inputRef.current).autocomplete('search');
    });
  }, []);
  return /*#__PURE__*/React.createElement("div", {
    className: "form-group"
  }, /*#__PURE__*/React.createElement("label", {
    htmlFor: "majors"
  }, "\u0E40\u0E25\u0E37\u0E2D\u0E01\u0E2A\u0E32\u0E02\u0E32"), /*#__PURE__*/React.createElement("input", {
    ref: inputRef,
    className: "form-control d-inline-block mb-2",
    id: "search-major",
    name: "search",
    type: "text",
    placeholder: "\u0E04\u0E49\u0E19\u0E2B\u0E32\u0E0A\u0E37\u0E48\u0E2D\u0E2A\u0E32\u0E02\u0E32"
  }), selectedMajors.length > 0 && /*#__PURE__*/React.createElement("table", {
    className: "table table-bordered"
  }, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("th", {
    scope: "col"
  }, "\u0E2A\u0E32\u0E02\u0E32"), /*#__PURE__*/React.createElement("th", {
    scope: "col"
  }, "\u0E08\u0E33\u0E19\u0E27\u0E19\u0E23\u0E31\u0E1A (\u0E04\u0E19)"), /*#__PURE__*/React.createElement("th", {
    scope: "col"
  }))), /*#__PURE__*/React.createElement("tbody", null, selectedMajors.map((major, idx) => {
    const label = major.title;
    return /*#__PURE__*/React.createElement("tr", {
      key: `major-${major.id}`
    }, /*#__PURE__*/React.createElement("td", {
      scope: "row"
    }, label, /*#__PURE__*/React.createElement("input", {
      value: major.id,
      type: "hidden",
      name: `majors_${idx + 1}_id`,
      required: true
    })), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("input", {
      type: "number",
      className: "form-control",
      name: `majors_${idx + 1}_slot`,
      defaultValue: major.slot,
      required: true
    })), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("button", {
      htmltype: "button",
      className: "btn btn-secondary",
      onClick: () => toggleMajor(major)
    }, "\u0E25\u0E1A")));
  }))));
};
const RequiredCriteria = ({
  initialTopics = []
}) => {
  const [topics, setTopics] = useState(initialTopics);
  const isCustomScoreCriteriaAllowed = _isCustomScoreCriteriaAllowed; //from global variable
  const addNewTopic = e => {
    e.preventDefault();
    const newTopic = topics.slice();
    newTopic.push({
      id: (() => Date.now())(),
      title: '',
      unit: '',
      children: []
    });
    console.log(newTopic);
    setTopics(newTopic);
  };
  const updateTopic = (topicId, value) => {
    console.log(`Updating topic`, topicId, value);
    const newTopics = topics.slice();
    const index = newTopics.findIndex(t => t.id === topicId);
    newTopics[index] = {
      ...newTopics[index],
      ...value
    };
    console.log('eiei', newTopics[index]);
    setTopics(newTopics);
  };
  const removeTopic = topic => {
    const newTopics = topics.slice();
    const index = newTopics.findIndex(t => t.id === topic.id);
    newTopics.splice(index, 1);
    setTopics(newTopics);
  };
  const setSecondaryTopics = (topicId, newSecondaryTopics) => {
    const newTopics = topics.slice();
    const index = newTopics.findIndex(t => t.id === topicId);
    newTopics[index] = {
      ...newTopics[index],
      children: newSecondaryTopics
    };
    console.log('new topic', newTopics[index]);
    setTopics(newTopics);
  };
  return /*#__PURE__*/React.createElement("div", {
    className: "form-group"
  }, /*#__PURE__*/React.createElement("label", {
    htmlFor: "majors"
  }, "\u0E04\u0E38\u0E13\u0E2A\u0E21\u0E1A\u0E31\u0E15\u0E34\u0E40\u0E09\u0E1E\u0E32\u0E30"), /*#__PURE__*/React.createElement("small", {
    className: "form-text text-muted"
  }, "\u0E04\u0E38\u0E13\u0E2A\u0E21\u0E1A\u0E31\u0E15\u0E34\u0E41\u0E25\u0E30\u0E04\u0E30\u0E41\u0E19\u0E19\u0E02\u0E31\u0E49\u0E19\u0E15\u0E48\u0E33 \u0E40\u0E0A\u0E48\u0E19 \u0E1C\u0E25\u0E01\u0E32\u0E23\u0E40\u0E23\u0E35\u0E22\u0E19\u0E40\u0E09\u0E25\u0E35\u0E48\u0E22\u0E2A\u0E30\u0E2A\u0E21 \u0E44\u0E21\u0E48\u0E19\u0E49\u0E2D\u0E22\u0E01\u0E27\u0E48\u0E32 2.0"), /*#__PURE__*/React.createElement("table", {
    className: "table table-bordered",
    style: {
      tableLayout: 'fixed'
    }
  }, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("th", {
    style: {
      width: '5%'
    }
  }), /*#__PURE__*/React.createElement("th", null), /*#__PURE__*/React.createElement("th", {
    style: {
      width: '15%'
    }
  }, "\u0E02\u0E31\u0E49\u0E19\u0E15\u0E48\u0E33 (\u2265)"), /*#__PURE__*/React.createElement("th", {
    style: {
      width: '15%'
    }
  }, "\u0E2B\u0E19\u0E48\u0E27\u0E22"), /*#__PURE__*/React.createElement("th", {
    style: {
      width: '5%'
    }
  }))), /*#__PURE__*/React.createElement("tbody", null, topics.map((topic, idx) => /*#__PURE__*/React.createElement(PrimaryTopic, {
    key: topic.id,
    topic: topic,
    removeTopic: removeTopic,
    updateTopic: updateTopic,
    number: idx + 1,
    secondaryTopics: topic.children,
    setSecondaryTopics: newSecondaryTopics => setSecondaryTopics(topic.id, newSecondaryTopics),
    isCustomScoreCriteriaAllowed: isCustomScoreCriteriaAllowed
  })), /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("div", {
    className: "btn btn-primary",
    onClick: addNewTopic
  }, "+")), /*#__PURE__*/React.createElement("td", null), /*#__PURE__*/React.createElement("td", null), /*#__PURE__*/React.createElement("td", null), /*#__PURE__*/React.createElement("td", null)))));
};
const ScoringCriteria = ({
  initialTopics = []
}) => {
  const isCustomScoreCriteriaAllowed = _isCustomScoreCriteriaAllowed; //from global variable

  const [topics, setTopics] = useState(initialTopics);
  const topicsRef = useRef(topics);
  useEffect(() => {
    topicsRef.current = topics;
  }, [topics]);
  const addNewTopic = e => {
    e.preventDefault();
    const newTopic = topicsRef.current.slice();
    newTopic.push({
      id: (() => Date.now())(),
      title: '',
      value: 1,
      children: []
    });
    console.log(newTopic);
    setTopics(newTopic);
  };
  const removeTopic = topic => {
    const newTopics = topicsRef.current.slice();
    const index = newTopics.findIndex(t => t.id === topic.id);
    newTopics.splice(index, 1);
    setTopics(newTopics);
  };
  const updateTopic = (topicId, value) => {
    console.log(`Updating topic`, topicId, value);
    const newTopics = topicsRef.current.slice();
    const index = newTopics.findIndex(t => t.id === topicId);
    newTopics[index] = {
      ...newTopics[index],
      ...value
    };
    setTopics(newTopics);
  };
  const setSecondaryTopics = (topicId, newSecondaryTopics) => {
    const newTopics = topicsRef.current.slice();
    const index = newTopics.findIndex(t => t.id === topicId);
    newTopics[index] = {
      ...newTopics[index],
      children: newSecondaryTopics
    };
    setTopics(newTopics);
  };
  const maxScore = topics.reduce((a, b) => a + b.value, 0);
  return /*#__PURE__*/React.createElement("div", {
    className: "form-group"
  }, /*#__PURE__*/React.createElement("label", {
    htmlFor: "majors"
  }, "\u0E40\u0E01\u0E13\u0E11\u0E4C\u0E01\u0E32\u0E23\u0E04\u0E31\u0E14\u0E40\u0E25\u0E37\u0E2D\u0E01"), !useComponentWeightType && /*#__PURE__*/React.createElement("small", {
    className: "form-text text-muted"
  }, "\u0E40\u0E01\u0E13\u0E11\u0E4C\u0E2A\u0E33\u0E2B\u0E23\u0E31\u0E1A\u0E04\u0E33\u0E19\u0E27\u0E19\u0E04\u0E30\u0E41\u0E19\u0E19 \u0E08\u0E31\u0E14\u0E25\u0E33\u0E14\u0E31\u0E1A \u0E40\u0E0A\u0E48\u0E19 GAT 50%, PAT-1 50%  \u0E2A\u0E33\u0E2B\u0E23\u0E31\u0E1A\u0E23\u0E2D\u0E1A\u0E17\u0E35\u0E48 1 \u0E16\u0E49\u0E32\u0E44\u0E21\u0E48\u0E15\u0E49\u0E2D\u0E07\u0E01\u0E32\u0E23\u0E23\u0E30\u0E1A\u0E38\u0E2A\u0E31\u0E14\u0E2A\u0E48\u0E27\u0E19\u0E43\u0E2B\u0E49\u0E43\u0E2A\u0E48 0"), useComponentWeightType && /*#__PURE__*/React.createElement("small", {
    className: "form-text text-muted"
  }, "\u0E2A\u0E33\u0E2B\u0E23\u0E31\u0E1A\u0E40\u0E01\u0E13\u0E11\u0E4C\u0E23\u0E2D\u0E1A Admission 2 \u0E43\u0E2B\u0E49\u0E40\u0E25\u0E37\u0E2D\u0E01\u0E41\u0E04\u0E48\u0E2D\u0E07\u0E04\u0E4C\u0E1B\u0E23\u0E30\u0E01\u0E2D\u0E1A\u0E40\u0E14\u0E35\u0E22\u0E27 (\u0E15\u0E2D\u0E19\u0E19\u0E35\u0E49\u0E43\u0E19\u0E23\u0E30\u0E1A\u0E1A\u0E2D\u0E32\u0E08\u0E40\u0E25\u0E37\u0E2D\u0E01\u0E44\u0E14\u0E49\u0E2B\u0E25\u0E32\u0E22\u0E40\u0E01\u0E13\u0E11\u0E4C \u0E41\u0E15\u0E48\u0E23\u0E1A\u0E01\u0E27\u0E19\u0E40\u0E25\u0E37\u0E2D\u0E01\u0E41\u0E04\u0E48\u0E2D\u0E31\u0E19\u0E40\u0E14\u0E35\u0E22\u0E27\u0E01\u0E48\u0E2D\u0E19) \u0E16\u0E49\u0E32\u0E21\u0E35\u0E01\u0E32\u0E23\u0E23\u0E31\u0E1A\u0E2B\u0E25\u0E32\u0E22\u0E23\u0E39\u0E1B\u0E41\u0E1A\u0E1A\u0E43\u0E2B\u0E49\u0E2A\u0E23\u0E49\u0E32\u0E07\u0E40\u0E07\u0E37\u0E48\u0E2D\u0E19\u0E44\u0E02\u0E01\u0E32\u0E23\u0E23\u0E31\u0E1A\u0E40\u0E1E\u0E34\u0E48\u0E21\u0E40\u0E15\u0E34\u0E21 \xA0 \u0E16\u0E49\u0E32\u0E15\u0E49\u0E2D\u0E07\u0E01\u0E32\u0E23\u0E41\u0E01\u0E49\u0E40\u0E01\u0E13\u0E11\u0E4C\u0E17\u0E35\u0E48\u0E40\u0E25\u0E37\u0E2D\u0E01\u0E41\u0E25\u0E49\u0E27\u0E42\u0E14\u0E22\u0E01\u0E32\u0E23\u0E40\u0E25\u0E37\u0E2D\u0E01\u0E43\u0E2B\u0E21\u0E48 \u0E43\u0E2B\u0E49\u0E25\u0E1A\u0E02\u0E49\u0E2D\u0E04\u0E27\u0E32\u0E21\u0E17\u0E34\u0E49\u0E07\u0E08\u0E30\u0E21\u0E35\u0E15\u0E31\u0E27\u0E40\u0E25\u0E37\u0E2D\u0E01\u0E02\u0E36\u0E49\u0E19\u0E21\u0E32\u0E41\u0E2A\u0E14\u0E07\u0E40\u0E2B\u0E21\u0E37\u0E2D\u0E19\u0E40\u0E14\u0E34\u0E21"), /*#__PURE__*/React.createElement("table", {
    className: "table table-bordered",
    style: {
      tableLayout: 'fixed'
    }
  }, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("th", {
    style: {
      width: '5%'
    }
  }), /*#__PURE__*/React.createElement("th", null), /*#__PURE__*/React.createElement("th", {
    style: {
      width: '15%'
    }
  }, "\u0E2A\u0E31\u0E14\u0E2A\u0E48\u0E27\u0E19\u0E04\u0E30\u0E41\u0E19\u0E19"), /*#__PURE__*/React.createElement("th", {
    style: {
      width: '15%'
    }
  }, "\u0E23\u0E49\u0E2D\u0E22\u0E25\u0E30"), /*#__PURE__*/React.createElement("th", {
    style: {
      width: '5%'
    }
  }))), /*#__PURE__*/React.createElement("tbody", null, topics.map((topic, idx) => /*#__PURE__*/React.createElement(PrimaryScoringTopic, {
    topic: topic,
    updateTopic: updateTopic,
    removeTopic: removeTopic,
    number: idx + 1,
    maxScore: maxScore,
    secondaryTopics: topic.children,
    setSecondaryTopics: newSecondaryTopics => setSecondaryTopics(topic.id, newSecondaryTopics),
    key: topic.id,
    isCustomScoreCriteriaAllowed: isCustomScoreCriteriaAllowed
  })), /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("div", {
    className: "btn btn-primary",
    onClick: addNewTopic
  }, "+")), /*#__PURE__*/React.createElement("td", null), /*#__PURE__*/React.createElement("td", null), /*#__PURE__*/React.createElement("td", null), /*#__PURE__*/React.createElement("td", null)))));
};
const PrimaryTopic = ({
  topic,
  removeTopic,
  number,
  updateTopic,
  secondaryTopics,
  setSecondaryTopics,
  isCustomScoreCriteriaAllowed
}) => {
  const secondaryTopicsRef = useRef(secondaryTopics);
  useEffect(() => {
    secondaryTopicsRef.current = secondaryTopics;
  }, [secondaryTopics]);
  const addNewTopic = e => {
    e.preventDefault();
    const newSecondaryTopics = secondaryTopicsRef.current.slice();
    newSecondaryTopics.push({
      id: (() => Date.now())(),
      title: ''
    });
    setSecondaryTopics(newSecondaryTopics);
  };
  const removeSecondaryTopic = topic => {
    const newSecondaryTopics = secondaryTopicsRef.current.slice();
    const index = newSecondaryTopics.findIndex(t => t.id === topic.id);
    newSecondaryTopics.splice(index, 1);
    setSecondaryTopics(newSecondaryTopics);
  };
  const updateSecondaryTopic = (topicId, value) => {
    const newSecondaryTopics = secondaryTopicsRef.current.slice();
    const index = newSecondaryTopics.findIndex(t => t.id === topicId);
    newSecondaryTopics[index] = {
      ...newSecondaryTopics[index],
      ...value
    };
    setSecondaryTopics(newSecondaryTopics);
  };
  const suffix = /*#__PURE__*/React.createElement("div", {
    className: "d-flex ml-2"
  }, secondaryTopics.length > 0 && /*#__PURE__*/React.createElement(SelectRelation, {
    name: `required_${number}_relation`,
    relations: relationRequired,
    className: "ml-2",
    value: topic.relation,
    onChange: event => {
      event.target.value !== topic.relation && updateTopic(topic.id, {
        relation: event.target.value
      });
    }
  }), /*#__PURE__*/React.createElement("button", {
    className: "btn btn-primary btn-sm ml-2",
    onClick: addNewTopic
  }, "+"));
  return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, number), isCustomScoreCriteriaAllowed ? /*#__PURE__*/React.createElement(EditableCell, {
    name: `required_${number}_title`
    // editable={mode === MODE.CREATE}
    ,
    initialValue: topic.title,
    focusOnMount: true,
    suffix: suffix,
    inputProps: {
      required: false
    },
    tags: requiredTags,
    name: `required_${number}_title`,
    onSave: v => {
      const tag = requiredTags.find(o => o.description === v);
      updateTopic(topic.id, {
        score_type: tag ? tag.score_type : 'OTHER',
        unit: tag ? tag.unit : ''
      });
    }
  }) : /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("div", {
    className: "d-flex align-items-baseline"
  }, /*#__PURE__*/React.createElement(SelectMenu, {
    name: `required_${number}_title`,
    initialValue: topic.title,
    inputProps: {
      required: false
    },
    choices: requiredTags.map(tag => ({
      value: tag.description,
      label: tag.description,
      ...tag
    })),
    onSave: v => {
      const tag = requiredTags.find(o => o.description === v);
      updateTopic(topic.id, {
        score_type: tag ? tag.score_type : 'OTHER',
        unit: tag ? tag.unit : ''
      });
    }
  }), suffix)), /*#__PURE__*/React.createElement(EditableCell, {
    name: `required_${number}_value`
    // editable={mode === MODE.CREATE}
    ,
    initialValue: topic.value
  }), /*#__PURE__*/React.createElement(EditableCell, {
    name: `required_${number}_unit`,
    editable: isCustomScoreCriteriaAllowed,
    initialValue: topic.unit || '',
    tags: unitTags
  }), /*#__PURE__*/React.createElement("input", {
    type: "hidden",
    name: `required_${number}_type`,
    value: topic.score_type || "OTHER",
    required: true
  }), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("button", {
    className: "btn btn-secondary btn-sm",
    onClick: () => removeTopic(topic)
  }, "-"))), secondaryTopics.map((secondaryTopic, idx) => {
    const snumber = `${number}.${idx + 1}`;
    const prefix = /*#__PURE__*/React.createElement("span", null, snumber, "\xA0\xA0");
    return /*#__PURE__*/React.createElement("tr", {
      key: secondaryTopic.id
    }, /*#__PURE__*/React.createElement("td", null), isCustomScoreCriteriaAllowed ? /*#__PURE__*/React.createElement(EditableCell, {
      name: `required_${snumber}_title`
      // editable={mode === MODE.CREATE}
      ,
      initialValue: secondaryTopic.title,
      focusOnMount: true,
      prefix: prefix,
      inputProps: {
        required: true
      },
      tags: requiredTags,
      onSave: v => {
        const tag = requiredTags.find(o => o.description === v);
        updateSecondaryTopic(secondaryTopic.id, {
          ...secondaryTopic,
          score_type: tag ? tag.score_type : 'OTHER',
          unit: tag ? tag.unit : ''
        });
      }
    }) : /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("div", {
      className: "d-flex align-items-baseline"
    }, prefix, /*#__PURE__*/React.createElement(SelectMenu, {
      name: `required_${snumber}_title`,
      initialValue: secondaryTopic.title,
      inputProps: {
        required: true
      },
      choices: requiredTags.map(tag => ({
        value: tag.description,
        label: tag.description,
        ...tag
      })),
      onSave: v => {
        const tag = requiredTags.find(o => o.description === v);
        updateSecondaryTopic(secondaryTopic.id, {
          ...secondaryTopic,
          score_type: tag ? tag.score_type : 'OTHER',
          unit: tag ? tag.unit : ''
        });
      }
    }))), /*#__PURE__*/React.createElement(EditableCell, {
      name: `required_${snumber}_value`
      // editable={mode === MODE.CREATE}
      ,
      initialValue: secondaryTopic.value
    }), /*#__PURE__*/React.createElement(EditableCell, {
      name: `required_${snumber}_unit`,
      editable: isCustomScoreCriteriaAllowed,
      initialValue: secondaryTopic.unit,
      tags: unitTags
    }), /*#__PURE__*/React.createElement("input", {
      type: "hidden",
      name: `required_${snumber}_type`,
      value: secondaryTopic.score_type || "OTHER",
      required: true
    }), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("button", {
      className: "btn btn-secondary btn-sm",
      onClick: () => removeSecondaryTopic(secondaryTopic)
    }, "-")));
  }));
};
const PrimaryScoringTopic = ({
  topic,
  removeTopic,
  number,
  updateTopic,
  maxScore,
  secondaryTopics,
  setSecondaryTopics,
  isCustomScoreCriteriaAllowed
}) => {
  const secondaryTopicsRef = useRef(secondaryTopics);
  useEffect(() => {
    secondaryTopicsRef.current = secondaryTopics;
  }, [secondaryTopics]);
  const addNewTopic = e => {
    e.preventDefault();
    const newSecondaryTopics = secondaryTopicsRef.current.slice();
    newSecondaryTopics.push({
      id: (() => (() => Date.now())())(),
      title: '',
      value: 1
    });
    setSecondaryTopics(newSecondaryTopics);
  };
  const removeSecondaryTopic = topic => {
    const newSecondaryTopics = secondaryTopicsRef.current.slice();
    const index = newSecondaryTopics.findIndex(t => t.id === topic.id);
    newSecondaryTopics.splice(index, 1);
    setSecondaryTopics(newSecondaryTopics);
  };
  const updateSecondaryTopic = (topicId, value) => {
    const newSecondaryTopics = secondaryTopicsRef.current.slice();
    const index = newSecondaryTopics.findIndex(t => t.id === topicId);
    newSecondaryTopics[index] = {
      ...newSecondaryTopics[index],
      ...value
    };
    setSecondaryTopics(newSecondaryTopics);
  };
  const primaryMaxScore = secondaryTopics.reduce((a, b) => a + b.value, 0);
  const suffix = /*#__PURE__*/React.createElement("div", {
    className: "d-flex"
  }, secondaryTopics.length > 0 && /*#__PURE__*/React.createElement(SelectRelation, {
    name: `scoring_${number}_relation`,
    relations: relationScoring,
    className: "ml-2",
    value: topic.relation,
    onChange: event => {
      event.target.value !== topic.relation && updateTopic(topic.id, {
        relation: event.target.value
      });
    }
  }), /*#__PURE__*/React.createElement("button", {
    className: "btn btn-primary btn-sm ml-2",
    onClick: addNewTopic
  }, "+"));
  return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, number), isCustomScoreCriteriaAllowed ? /*#__PURE__*/React.createElement(EditableCell, {
    name: `scoring_${number}_title`
    // editable={mode === MODE.CREATE}
    ,
    initialValue: topic.title,
    focusOnMount: true,
    suffix: suffix,
    inputProps: {
      required: false
    },
    tags: scoringTags,
    onSave: v => {
      const tag = scoringTags.find(o => o.description === v);
      updateTopic(topic.id, {
        score_type: tag ? tag.score_type : 'OTHER'
      });
    }
  }) : /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("div", {
    className: "d-flex align-items-baseline"
  }, /*#__PURE__*/React.createElement(SelectMenu, {
    name: `scoring_${number}_title`,
    initialValue: topic.title,
    inputProps: {
      required: false
    },
    choices: scoringTags.map(tag => ({
      value: tag.description,
      label: tag.description,
      ...tag
    })),
    onSave: v => {
      const tag = scoringTags.find(o => o.description === v);
      updateTopic(topic.id, {
        score_type: tag ? tag.score_type : 'OTHER'
      });
    }
  }), suffix)), /*#__PURE__*/React.createElement(EditableCell, {
    name: `scoring_${number}_value`
    // editable={mode === MODE.CREATE}
    ,
    initialValue: topic.value,
    onSave: v => {
      updateTopic(topic.id, {
        value: parseInt(v)
      });
    },
    inputType: "number",
    inputProps: {
      required: true
    }
  }), /*#__PURE__*/React.createElement("input", {
    type: "hidden",
    name: `scoring_${number}_type`,
    value: topic.score_type || "OTHER",
    required: true
  }), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("strong", null, (topic.value / maxScore * 100).toLocaleString(), "%")), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("button", {
    className: "btn btn-secondary btn-sm",
    onClick: () => removeTopic(topic)
  }, "-"))), secondaryTopics.map((secondaryTopic, idx) => {
    const snumber = `${number}.${idx + 1}`;
    const prefix = /*#__PURE__*/React.createElement("span", null, number, ".", idx + 1, "\xA0\xA0");
    return /*#__PURE__*/React.createElement("tr", {
      key: secondaryTopic.id
    }, /*#__PURE__*/React.createElement("td", null), isCustomScoreCriteriaAllowed ? /*#__PURE__*/React.createElement(EditableCell, {
      name: `scoring_${snumber}_title`
      // editable={mode === MODE.CREATE}
      ,
      initialValue: secondaryTopic.title,
      focusOnMount: true,
      prefix: prefix,
      inputProps: {
        required: true
      },
      tags: scoringTags,
      onSave: v => {
        const tag = scoringTags.find(o => o.description === v);
        updateSecondaryTopic(secondaryTopic.id, {
          ...secondaryTopic,
          score_type: tag ? tag.score_type : 'OTHER'
        });
      }
    }) : /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("div", {
      className: "d-flex align-items-baseline"
    }, prefix, /*#__PURE__*/React.createElement(SelectMenu, {
      name: `scoring_${snumber}_title`,
      initialValue: secondaryTopic.title,
      inputProps: {
        required: true
      },
      choices: scoringTags.map(tag => ({
        value: tag.description,
        label: tag.description,
        ...tag
      })),
      onSave: v => {
        const tag = scoringTags.find(o => o.description === v);
        updateSecondaryTopic(secondaryTopic.id, {
          ...secondaryTopic,
          score_type: tag ? tag.score_type : 'OTHER'
        });
      }
    }))), topic.relation === RELATION_MAX ? /*#__PURE__*/React.createElement("td", null) : /*#__PURE__*/React.createElement(EditableCell, {
      name: `scoring_${snumber}_value`
      // editable={mode === MODE.CREATE}
      ,
      initialValue: secondaryTopic.value,
      onSave: v => {
        updateSecondaryTopic(secondaryTopic.id, {
          value: parseInt(v)
        });
      },
      inputType: "number",
      inputProps: {
        required: true
      }
    }), /*#__PURE__*/React.createElement("input", {
      type: "hidden",
      name: `scoring_${snumber}_type`,
      value: secondaryTopic.score_type || "OTHER",
      required: true
    }), /*#__PURE__*/React.createElement("td", null, topic.relation !== RELATION_MAX && `${(secondaryTopic.value / primaryMaxScore * 100).toLocaleString()}%`), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("button", {
      className: "btn btn-secondary btn-sm",
      onClick: () => removeSecondaryTopic(secondaryTopic)
    }, "-")));
  }));
};
const EditableCell = ({
  value,
  initialValue,
  editable = true,
  focusOnMount = false,
  children,
  onSave,
  prefix,
  suffix,
  inputType,
  name,
  inputProps,
  tags = [],
  ...restProps
}) => {
  const inputRef = useRef();
  useEffect(() => {
    if (editable) {
      $(inputRef.current).autocomplete({
        source: typeof tags[0] === 'string' ? tags :
        // for required and scoring tags
        // TODO: refactor this
        tags.map(o => ({
          label: o.description,
          value: o.description,
          onSelect: () => {
            let temp = name.split('_');
            temp[temp.length - 1] = 'unit';
            const unitName = temp.join('_');
            const unitEl = $(`[name="${unitName}"]`)[0];
            if (unitEl) {
              unitEl.value = o.unit;
            }
          }
        })),
        minLength: 0,
        select: (event, ui) => {
          ui.item.onSelect && ui.item.onSelect();
        }
      }).focus(function () {
        if (inputRef.current.value == "") {
          $(inputRef.current).autocomplete("search");
        }
      });
    } else {}
  }, [editable]);
  useEffect(() => {
    if (focusOnMount && !initialValue) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [focusOnMount]);
  const save = e => {
    try {
      onSave && onSave(inputRef.current.value);
    } catch (errInfo) {
      console.log('Save failed:', errInfo);
    }
  };
  const calHeight = () => {
    inputRef.current.style.height = "";
    inputRef.current.style.height = inputRef.current.scrollHeight + 'px';
  };
  useEffect(() => {
    if (editable) {
      calHeight();
    }
  }, []);
  let childNode = /*#__PURE__*/React.createElement("input", _extends({
    type: inputType,
    name: name,
    className: "form-control d-inline-block",
    defaultValue: initialValue,
    tabIndex: -1,
    style: {
      pointerEvents: 'none'
    }
  }, inputProps));
  if (editable) {
    childNode = /*#__PURE__*/React.createElement("div", {
      className: "d-flex align-items-baseline"
    }, prefix, inputType === 'number' ? /*#__PURE__*/React.createElement("input", _extends({
      type: "number",
      name: name,
      className: "form-control d-inline-block",
      ref: inputRef,
      onChange: save,
      onBlur: save,
      defaultValue: initialValue
    }, inputProps)) : /*#__PURE__*/React.createElement("textarea", _extends({
      className: "form-control d-inline-block",
      rows: 1,
      name: name,
      ref: inputRef,
      onChange: calHeight,
      onBlur: save,
      defaultValue: initialValue
    }, inputProps)), suffix);
  }
  return /*#__PURE__*/React.createElement("td", _extends({
    style: editable ? {
      cursor: 'pointer'
    } : {}
  }, restProps), " ", childNode);
};
const SelectRelation = ({
  name,
  relations,
  className,
  value,
  onChange
}) => {
  return /*#__PURE__*/React.createElement("select", {
    name: name,
    id: name,
    className: className,
    value: value,
    onChange: onChange
  }, /*#__PURE__*/React.createElement("option", {
    disabled: true,
    selected: true,
    value: ""
  }, "\u0E40\u0E25\u0E37\u0E2D\u0E01\u0E04\u0E27\u0E32\u0E21\u0E2A\u0E31\u0E21\u0E1E\u0E31\u0E19\u0E18\u0E4C"), relations.map(r => /*#__PURE__*/React.createElement("option", {
    value: r.value,
    key: r.value
  }, r.label)));
};
const SelectMenu = ({
  name,
  choices,
  className,
  initialValue,
  inputProps,
  onSave
}) => {
  const inputRef = useRef();
  useEffect(() => {
    $(inputRef.current).selectmenu({
      classes: {
        'ui-selectmenu-button': 'flex-1'
      },
      select: (event, ui) => {
        onSave && onSave(inputRef.current.value);
        const name = event.target.name;
        const o = choices.find(choice => choice.value === ui.item.value);
        // console.log('name: ', name)
        // console.log('o: ', o)
        if (!o) return;
        let temp = name.split('_');
        temp[temp.length - 1] = 'unit';
        const unitName = temp.join('_');
        const unitEl = $(`[name="${unitName}"]`)[0];
        if (unitEl) {
          unitEl.value = o.unit;
        }
      }
    }).selectmenu("menuWidget").addClass("overflow");
  }, []);
  return /*#__PURE__*/React.createElement("select", _extends({
    name: name,
    id: name,
    defaultValue: initialValue || null,
    ref: inputRef,
    rows: 1
  }, inputProps), /*#__PURE__*/React.createElement("option", {
    disabled: inputProps.required,
    selected: true,
    value: "",
    key: ""
  }, inputProps.required ? 'กรุณาเลือก' : ''), choices.map(r => /*#__PURE__*/React.createElement("option", {
    value: r.value,
    key: r.value
  }, r.label)));
};
const domContainer = document.querySelector('#add-criterion-form');
ReactDOM.render(e(Form), domContainer);