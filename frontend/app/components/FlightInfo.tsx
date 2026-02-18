import React from 'react';

type FlightInfoProps = {
  data: {
    intro: string;
    outbound: {
      airline: string;
      date: string;
      departure: string;
      arrival: string;
      duration: string;
      stops: string;
    };
    return: {
      airline: string;
      date: string;
      departure: string;
      arrival: string;
      duration: string;
      stops: string;
    };
    total_price: string;
    booking_link: string;
  };
};

const FlightInfo: React.FC<FlightInfoProps> = ({ data }) => {
  return (
    <div>
      <p>{data.intro}</p>
      <ul className="list-disc pl-5 mt-2">
        <li>
          <strong>Outbound:</strong>
          <ul className="list-disc pl-5">
            <li>Airline: {data.outbound.airline}</li>
            <li>Date: {data.outbound.date}</li>
            <li>Departure: {data.outbound.departure}</li>
            <li>Arrival: {data.outbound.arrival}</li>
            <li>Duration: {data.outbound.duration}</li>
            <li>Stops: {data.outbound.stops}</li>
          </ul>
        </li>
        <li className="mt-2">
          <strong>Return:</strong>
          <ul className="list-disc pl-5">
            <li>Airline: {data.return.airline}</li>
            <li>Date: {data.return.date}</li>
            <li>Departure: {data.return.departure}</li>
            <li>Arrival: {data.return.arrival}</li>
            <li>Duration: {data.return.duration}</li>
            <li>Stops: {data.return.stops}</li>
          </ul>
        </li>
      </ul>
      <p className="mt-2">
        <strong>Total Price:</strong> {data.total_price}
      </p>
      <a
        href={data.booking_link}
        target="_blank"
        rel="noopener noreferrer"
        className="text-blue-400 hover:underline mt-2 inline-block"
      >
        Click here to book your flight
      </a>
    </div>
  );
};

export default FlightInfo;
