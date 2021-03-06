import React, {PropTypes} from 'react'
import RoomCard from './RoomCard'
import DateRangeSelector from './DateRangeSelector'
import AvailabilityMatrix from './AvailabilityMatrix'
import { FormGroup, Checkbox, Button, Nav, NavItem } from 'react-bootstrap';
import { isFullyAvailable } from '../../models/Availabilities'

export default class RoomCards extends React.Component {
  static propTypes = {
    rooms: PropTypes.array.isRequired
  }

  renderRoomCards() {
    return this.props.rooms.map((room) => {
      return <RoomCard key={room.id} routeParams={this.props.routeParams} query={this.props.query} {...room} />
    })
  }

  render() {
    if (this.props.rooms.length > 0) {
      return (
        <div className="row" id="room-cards">
          {this.renderRoomCards()}
        </div>
      )
    } else {
      if (this.props.loading) {
        return null
      } else {
        return <div className="no-data" style={{marginTop: '100px'}}>Sorry, no rooms match your search</div>
      }
    }
  }
}
