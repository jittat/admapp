'use strict';

const e = React.createElement;
const { useState } = React

const majors = [
  {
    program_id: '10020112610501A',
    faculty_name_th: 'คณะบริหารธุรกิจ',
    program_name_th: 'บช.บ.',
    program_type_name_th: 'ภาษาไทย ปกติ',
  },
  {
    program_id: '10020111901802B',
    faculty_name_th: 'คณะมนุษยศาสตร์',
    program_name_th: 'ศศ.บ. สาขาวิชาภาษาจีนธุรกิจ',
    program_type_name_th: 'ภาษาไทย พิเศษ',
  },
  {
    program_id: '10020104212701A',
    faculty_name_th: 'คณะวิทยาศาสตร์',
    program_name_th: 'วท.บ. สาขาวิชาฟิสิกส์',
    program_type_name_th: 'ภาษาไทย ปกติ',
  },

  {
    program_id: '10020104220201B',
    faculty_name_th: 'คณะวิทยาศาสตร์',
    program_name_th: 'วท.บ. สาขาวิชาวิทยาการคอมพิวเตอร์',
    program_type_name_th: 'ภาษาไทย ปกติ',
  },
  {
    program_id: '10020104210702A',
    faculty_name_th: 'คณะวิทยาศาสตร์',
    program_name_th: 'วท.บ. สาขาวิชาวิทยาศาสตร์ชีวภาพรังสี',
    program_type_name_th: 'ภาษาไทย พิเศษ',
  },
  {
    program_id: '10020104213301A',
    faculty_name_th: 'คณะวิทยาศาสตร์',
    program_name_th: 'วท.บ. สาขาวิชาสถิติ',
    program_type_name_th: 'ภาษาไทย ปกติ',
  }
]
const Form = () => {
  const [search, setSearch] = useState('')
  const [selectedMajors, setSelectedMajors] = useState([])
  const selectMajor = (major) => {
    const newSelectedMajors = selectedMajors.slice()
    const index = newSelectedMajors.findIndex((m) => m.program_id === major.program_id)
    if (index > -1) {
      newSelectedMajors.splice(index, 1)
    } else {
      newSelectedMajors.push(major)
    }
    setSelectedMajors(newSelectedMajors)
  }
  return (
    <div>
      <form>
        <div className="form-group">
          <label htmlFor="majors">เลือกสาขา</label>
          <input
            type="text"
            id="majors"
            className="form-control"
            onKeyUp={(e) => { setSearch((e.target.value).toUpperCase()) }}
            placeholder="ค้นหาชื่อคณะ/สาขา"
          />
          <div className="list-group" style={{ zIndex: 1, height: 300, overflow: 'auto' }}>
            {majors.map(major => {
              const label = `${major.faculty_name_th} ${major.program_name_th}`
              if (label.toUpperCase().indexOf(search) > -1)
                return (
                  <a
                    href="#"
                    key={major.program_id}
                    className="list-group-item list-group-item-action"
                    onClick={() => { selectMajor(major) }}
                  >{label}</a>
                )
            })}
          </div>
        </div>
        {selectedMajors.map(major => {
          const label = `${major.faculty_name_th} ${major.program_name_th}`
          return (
            <div>{label}</div>
          )
        })}
      </form>
    </div>
  )
}

const domContainer = document.querySelector('#add-criterion-form');
ReactDOM.render(e(Form), domContainer);