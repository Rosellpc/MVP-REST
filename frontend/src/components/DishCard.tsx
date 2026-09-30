type DishCardProps = {
    name: string;
    category: string;
    price: string;
    image_url: string;
};

export default function DishCard({
    name, category, price, image_url,
}: DishCardProps) {
    return (
        <article className="property-card">
            <img src={image_url} alt={name} />
            <div className="property-card-content">
                <h4>{name}</h4>
                <p>{category}</p>
                <strong>
                    s/ {Number(price).toFixed(2)}
                </strong>
            </div>
        </article>
    )
}

